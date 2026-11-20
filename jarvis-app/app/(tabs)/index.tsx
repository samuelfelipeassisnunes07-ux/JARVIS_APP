import * as DocumentPicker from 'expo-document-picker';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useRef, useState } from "react";
import {
  Alert,
  Animated,
  Easing,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View
} from "react-native";
import { useTheme } from "../../context/ThemeContext";

type Message = {
  id: string;
  text: string;
  isUser?: boolean;
  time: string;
};

// Componente de mensagem
const MessageItem = ({ item, index }: { item: Message; index: number }) => {
  const { darkMode } = useTheme();
  const messageFade = useRef(new Animated.Value(0)).current;
  const messageSlide = useRef(new Animated.Value(item.isUser ? 50 : -50)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(messageFade, {
        toValue: 1,
        duration: 500,
        delay: index * 100,
        useNativeDriver: true
      }),
      Animated.spring(messageSlide, {
        toValue: 0,
        tension: 50,
        friction: 7,
        useNativeDriver: true
      })
    ]).start();
  }, [messageFade, messageSlide, index]);

  return (
    <Animated.View
      style={[
        styles.messageContainer,
        item.isUser ? styles.userMessageContainer : styles.botMessageContainer,
        {
          opacity: messageFade,
          transform: [{ translateX: messageSlide }]
        }
      ]}
    >
      <View style={[
        styles.message,
        item.isUser ? styles.userMessage : styles.botMessage,
        item.isUser ? null : (darkMode && styles.botMessageDark)
      ]}>
        <Text style={[
          styles.messageText,
          item.isUser && styles.userMessageText,
          !item.isUser && darkMode && styles.messageTextDark
        ]}>
          {item.text}
        </Text>
        <Text style={[
          styles.timestamp,
          item.isUser && styles.userTimestamp,
          !item.isUser && darkMode && styles.timestampDark
        ]}>
          {item.time}
        </Text>
      </View>
    </Animated.View>
  );
};

export default function Home() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Sou o Jarvis, o que você manda para hoje?',
      isUser: false,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [loading, setLoading] = useState(false);
  const { darkMode } = useTheme();
  
  // Animações
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;
  const buttonScale = useRef(new Animated.Value(1)).current;
  const inputBorderColor = useRef(new Animated.Value(0)).current;

  // Efeito de entrada inicial
  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
        easing: Easing.ease
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 50,
        friction: 7,
        useNativeDriver: true
      })
    ]).start();
  }, [fadeAnim, slideAnim]);

  const flatListRef = useRef<FlatList>(null);

  const pickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: 'application/pdf',
      });

      if (!result.canceled) {
        uploadPDF(result.assets[0]);
      }

    } catch (error) {
      console.log("Erro ao pegar PDF:", error);
      Alert.alert("Erro", "Não foi possível selecionar o arquivo PDF");
    }
  };

  const uploadPDF = async (file: any) => {
    const formData = new FormData();

    formData.append('file', {
      uri: file.uri,
      name: file.name,
      type: 'application/pdf',
    } as any);

    try {
      const response = await fetch("https://insipient-tai-unprisonable.ngrok-free.dev/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      const botMessage: Message = {
        id: Date.now().toString(),
        text: data.message || data.response || "📄 PDF enviado com sucesso!",
        isUser: false,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      setMessages(prev => [...prev, botMessage]);
      
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);

    } catch (error) {
      console.log("Erro ao enviar PDF:", error);
      Alert.alert("Erro", "Não foi possível enviar o PDF. Verifique a conexão com o servidor.");
    }
  };

  const sendMessage = async () => {
    if (message.trim() === "") return;

    Animated.sequence([
      Animated.spring(buttonScale, {
        toValue: 0.8,
        useNativeDriver: true,
        speed: 20
      }),
      Animated.spring(buttonScale, {
        toValue: 1,
        useNativeDriver: true,
        speed: 20
      })
    ]).start();

    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    const userMessage: Message = {
      id: Date.now().toString(),
      text: message,
      isUser: true,
      time: currentTime
    };
    
    setMessages(prevMessages => [...prevMessages, userMessage]);
    setMessage("");
    setLoading(true);

    try {
      const response = await fetch("https://insipient-tai-unprisonable.ngrok-free.dev/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          text: message,
          session_id: "mobile_user"
        })
      });

      if (!response.ok) {
        throw new Error(`Erro na API: ${response.status}`);
      }

      const data = await response.json();
      
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.response || data.message || "Resposta recebida",
        isUser: false,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      
      setMessages(prevMessages => [...prevMessages, botMessage]);
      
    } catch (error) {
      console.error("Erro ao enviar mensagem:", error);
      Alert.alert(
        "Erro de Conexão",
        "Não foi possível conectar ao servidor. Verifique se o backend está rodando."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView 
      style={[
        styles.container,
        darkMode && styles.containerDark
      ]}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={Platform.OS === "ios" ? 90 : 0}
    >
      <StatusBar style={darkMode ? "light" : "dark"} />
      
      <Animated.View style={[
        styles.header,
        darkMode && styles.headerDark,
        { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }
      ]}>
        <View style={styles.headerContent}>
          <View style={styles.headerLeft}>
            <View style={styles.statusDot} />
            <Text style={[
              styles.headerTitle,
              darkMode && styles.headerTitleDark
            ]}>Jarvis</Text>
          </View>
          <View style={styles.headerRight}>
            <View style={[
              styles.onlineBadge,
              darkMode && styles.onlineBadgeDark
            ]}>
              <Text style={styles.onlineText}>Online</Text>
            </View>
          </View>
        </View>
      </Animated.View>

      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item, index }) => (
          <MessageItem item={item} index={index} />
        )}
        contentContainerStyle={styles.messagesList}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled"
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
      />

      <Animated.View style={[
        styles.inputArea,
        darkMode && styles.inputAreaDark,
        { 
          borderColor: inputBorderColor.interpolate({
            inputRange: [0, 1],
            outputRange: darkMode ? ['#374151', '#818cf8'] : ['#e5e7eb', '#6366f1']
          })
        }
      ]}>
        <TextInput
          style={[
            styles.input,
            darkMode && styles.inputDark
          ]}
          placeholder="Digite sua mensagem..."
          placeholderTextColor={darkMode ? "#6b7280" : "#9ca3af"}
          value={message}
          onChangeText={setMessage}
          editable={!loading}
          multiline
          onFocus={() => {
            Animated.timing(inputBorderColor, {
              toValue: 1,
              duration: 300,
              useNativeDriver: false
            }).start();
          }}
          onBlur={() => {
            Animated.timing(inputBorderColor, {
              toValue: 0,
              duration: 300,
              useNativeDriver: false
            }).start();
          }}
        />

        {/* BOTÃO PDF */}
        <TouchableOpacity 
          style={[styles.button, { backgroundColor: "#10b981" }]} 
          onPress={pickDocument}
        >
          <Text style={styles.buttonText}>📎</Text>
        </TouchableOpacity>

        {/* BOTÃO ENVIAR */}
        <Animated.View style={{ transform: [{ scale: buttonScale }] }}>
          <TouchableOpacity 
            style={[
              styles.button,
              loading && styles.buttonDisabled,
              darkMode && styles.buttonDark
            ]} 
            onPress={sendMessage}
            disabled={loading || !message.trim()}
            activeOpacity={0.7}
          >
            <Text style={styles.buttonText}>
              {loading ? "..." : "➤"}
            </Text>
          </TouchableOpacity>
        </Animated.View>
      </Animated.View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#f3f4f6",
  },
  containerDark: {
    backgroundColor: "#111827",
  },
  header: {
    backgroundColor: "#6366f1",
    paddingTop: 50,
    paddingBottom: 20,
    paddingHorizontal: 20,
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
    shadowColor: "#6366f1",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  headerDark: {
    backgroundColor: "#4f46e5",
    shadowColor: "#4f46e5",
  },
  headerContent: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  headerLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  headerRight: {
    flexDirection: "row",
    alignItems: "center",
  },
  statusDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: "#4ade80",
    marginRight: 8,
  },
  headerTitle: {
    color: "#fff",
    fontSize: 24,
    fontWeight: "bold",
  },
  headerTitleDark: {
    color: "#fff",
  },
  onlineBadge: {
    backgroundColor: "rgba(255,255,255,0.2)",
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  onlineBadgeDark: {
    backgroundColor: "rgba(255,255,255,0.15)",
  },
  onlineText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "600",
  },
  messagesList: {
    padding: 20,
    paddingBottom: 10,
    flexGrow: 1,
  },
  messageContainer: {
    marginBottom: 15,
    maxWidth: "80%",
  },
  userMessageContainer: {
    alignSelf: "flex-end",
  },
  botMessageContainer: {
    alignSelf: "flex-start",
  },
  message: {
    padding: 15,
    borderRadius: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  userMessage: {
    backgroundColor: "#6366f1",
    borderBottomRightRadius: 5,
  },
  botMessage: {
    backgroundColor: "#fff",
    borderBottomLeftRadius: 5,
  },
  botMessageDark: {
    backgroundColor: "#1f2937",
  },
  messageText: {
    color: "#1f2937",
    fontSize: 16,
    lineHeight: 22,
  },
  messageTextDark: {
    color: "#f9fafb",
  },
  userMessageText: {
    color: "#ffffff",
  },
  timestamp: {
    color: "rgba(0,0,0,0.4)",
    fontSize: 11,
    marginTop: 5,
    alignSelf: "flex-end",
  },
  timestampDark: {
    color: "rgba(255,255,255,0.4)",
  },
  userTimestamp: {
    color: "rgba(255,255,255,0.7)",
  },
  inputArea: {
    flexDirection: "row",
    padding: 15,
    backgroundColor: "#fff",
    borderTopWidth: 1,
    borderColor: "#e5e7eb",
    alignItems: "flex-end",
    gap: 10,
  },
  inputAreaDark: {
    backgroundColor: "#1f2937",
    borderColor: "#374151",
  },
  input: {
    flex: 1,
    backgroundColor: "#f9fafb",
    borderRadius: 25,
    paddingHorizontal: 20,
    paddingVertical: 12,
    paddingRight: 15,
    maxHeight: 100,
    fontSize: 16,
    color: "#1f2937",
    borderWidth: 1,
    borderColor: "#e5e7eb",
  },
  inputDark: {
    backgroundColor: "#374151",
    borderColor: "#4b5563",
    color: "#f9fafb",
  },
  button: {
    backgroundColor: "#6366f1",
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: "center",
    alignItems: "center",
    marginLeft: 10,
    shadowColor: "#6366f1",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  buttonDark: {
    backgroundColor: "#818cf8",
    shadowColor: "#818cf8",
  },
  buttonDisabled: {
    backgroundColor: "#9ca3af",
    shadowColor: "#6b7280",
  },
  buttonText: {
    color: "#fff",
    fontWeight: "bold",
    fontSize: 18,
  },
});