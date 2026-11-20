# tools/fine_tuning.py
"""
Ferramentas para fine-tuning de modelos de IA.
Suporte para LoRA/QLoRA com Hugging Face e Ollama.
"""

import os
import json
import torch
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from database.feedback import FeedbackManager
import logging

logger = logging.get_logger(__name__)

@dataclass
class FineTuningConfig:
    """Configuração para fine-tuning."""
    model_name: str = "microsoft/DialoGPT-medium"
    output_dir: str = "./models/fine_tuned"
    num_epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 5e-5
    max_length: int = 512
    lora_r: int = 8
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    use_qlora: bool = True  # Usar QLoRA para economia de memória

class FineTuningManager:
    """Gerenciador de fine-tuning para modelos de IA."""

    def __init__(self, config: Optional[FineTuningConfig] = None):
        self.config = config or FineTuningConfig()
        self.feedback_manager = FeedbackManager()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def prepare_training_data(self, min_rating: int = 4) -> List[Dict]:
        """
        Prepara dados de treinamento a partir do feedback positivo.

        Args:
            min_rating: Rating mínimo para incluir no treinamento (1-5)

        Returns:
            Lista de exemplos de treinamento
        """
        logger.info(f"Coletando feedback com rating >= {min_rating}")

        # Busca feedback positivo
        feedback_data = self.feedback_manager.get_recent_feedback(limit=1000)

        training_examples = []

        for item in feedback_data:
            if item['rating'] >= min_rating:
                # Cria exemplo de treinamento no formato conversa
                example = {
                    "instruction": item['user_question'],
                    "response": item['assistant_response'],
                    "intent": item.get('intent', ''),
                    "context": f"Intenção detectada: {item.get('intent', 'geral')}"
                }
                training_examples.append(example)

        logger.info(f"Encontrados {len(training_examples)} exemplos de treinamento")
        return training_examples

    def save_training_data(self, examples: List[Dict], output_file: str = "training_data.jsonl"):
        """Salva dados de treinamento em formato JSONL."""
        output_path = Path(self.config.output_dir) / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            for example in examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')

        logger.info(f"Dados salvos em {output_path}")
        return str(output_path)

    def create_lora_config(self) -> LoraConfig:
        """Cria configuração LoRA para fine-tuning eficiente."""
        return LoraConfig(
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
        )

    def load_model_and_tokenizer(self):
        """Carrega modelo e tokenizer."""
        logger.info(f"Carregando modelo: {self.config.model_name}")

        tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        # Configuração para QLoRA (quantização)
        if self.config.use_qlora:
            from transformers import BitsAndBytesConfig
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True
            )

            model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                quantization_config=bnb_config,
                device_map="auto",
                torch_dtype=torch.float16
            )

            model = prepare_model_for_kbit_training(model)
        else:
            model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                torch_dtype=torch.float16,
                device_map="auto"
            )

        return model, tokenizer

    def tokenize_function(self, examples, tokenizer):
        """Função de tokenização para o dataset."""
        texts = []
        for example in examples:
            # Formatar como conversa
            text = f"Usuário: {example['instruction']}\nAssistente: {example['response']}"
            texts.append(text)

        return tokenizer(
            texts,
            truncation=True,
            padding="max_length",
            max_length=self.config.max_length,
            return_tensors="pt"
        )

    def fine_tune_model(self, training_data_path: str):
        """
        Executa o fine-tuning do modelo.

        Args:
            training_data_path: Caminho para o arquivo de dados de treinamento
        """
        try:
            # Carrega modelo e tokenizer
            model, tokenizer = self.load_model_and_tokenizer()

            # Aplica LoRA
            lora_config = self.create_lora_config()
            model = get_peft_model(model, lora_config)

            logger.info(f"Modelo preparado com LoRA. Parâmetros treináveis: {model.print_trainable_parameters()}")

            # Carrega dados de treinamento
            from datasets import load_dataset
            dataset = load_dataset("json", data_files=training_data_path, split="train")

            # Tokeniza dataset
            tokenized_dataset = dataset.map(
                lambda x: self.tokenize_function(x, tokenizer),
                batched=True,
                remove_columns=dataset.column_names
            )

            # Configuração do treinamento
            training_args = TrainingArguments(
                output_dir=self.config.output_dir,
                num_train_epochs=self.config.num_epochs,
                per_device_train_batch_size=self.config.batch_size,
                gradient_accumulation_steps=4,
                learning_rate=self.config.learning_rate,
                fp16=True,
                save_total_limit=2,
                save_steps=500,
                logging_steps=100,
                evaluation_strategy="no",
                save_strategy="steps",
                load_best_model_at_end=False,
            )

            # Data collator
            data_collator = DataCollatorForLanguageModeling(
                tokenizer=tokenizer,
                mlm=False
            )

            # Trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset,
                data_collator=data_collator,
            )

            logger.info("Iniciando treinamento...")
            trainer.train()

            # Salva o modelo
            model.save_pretrained(self.config.output_dir)
            tokenizer.save_pretrained(self.config.output_dir)

            logger.info(f"Modelo fine-tuned salvo em {self.config.output_dir}")

            return True

        except Exception as e:
            logger.error(f"Erro no fine-tuning: {e}")
            return False

    def export_for_ollama(self, model_path: str, model_name: str = "jarvis-fine-tuned"):
        """
        Exporta modelo fine-tuned para formato Ollama.

        Args:
            model_path: Caminho do modelo fine-tuned
            model_name: Nome do modelo no Ollama
        """
        try:
            # Comando para criar Modelfile do Ollama
            modelfile_content = f"""
FROM {model_path}
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
SYSTEM "Você é Jarvis, um assistente pessoal inteligente com memória de longo prazo."
"""

            modelfile_path = Path(model_path) / "Modelfile"
            with open(modelfile_path, 'w') as f:
                f.write(modelfile_content)

            logger.info(f"Modelfile criado: {modelfile_path}")
            logger.info(f"Para usar no Ollama: ollama create {model_name} -f {modelfile_path}")

            return str(modelfile_path)

        except Exception as e:
            logger.error(f"Erro ao exportar para Ollama: {e}")
            return None

# Função utilitária para executar fine-tuning completo
def run_fine_tuning_pipeline(min_rating: int = 4, model_name: str = "microsoft/DialoGPT-medium"):
    """
    Pipeline completo de fine-tuning:
    1. Coleta feedback positivo
    2. Prepara dados de treinamento
    3. Executa fine-tuning
    4. Exporta para Ollama
    """
    config = FineTuningConfig(model_name=model_name)
    manager = FineTuningManager(config)

    # Passo 1: Preparar dados
    training_examples = manager.prepare_training_data(min_rating)
    if not training_examples:
        logger.warning("Nenhum dado de treinamento encontrado. Colete mais feedback primeiro.")
        return False

    training_file = manager.save_training_data(training_examples)

    # Passo 2: Fine-tuning
    success = manager.fine_tune_model(training_file)

    if success:
        # Passo 3: Exportar para Ollama
        modelfile = manager.export_for_ollama(config.output_dir)
        logger.info("Fine-tuning concluído com sucesso!")
        logger.info(f"Modelfile gerado: {modelfile}")
        return True

    return False

if __name__ == "__main__":
    # Exemplo de uso
    print("Iniciando pipeline de fine-tuning...")
    run_fine_tuning_pipeline()