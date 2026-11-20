import { StatusBar } from 'expo-status-bar';
import { useEffect, useRef, useState } from "react";
import {
  Animated,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useTheme } from "../../context/ThemeContext";

type Feature = {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
};

const features: Feature[] = [
  {
    id: '1',
    title: '🤖 IA Avançada',
    description: 'Converse com uma IA treinada para ajudar você em diversas tarefas',
    icon: '🤖',
    color: '#6366f1',
  },
  {
    id: '2',
    title: '⚡ Respostas Rápidas',
    description: 'Processamento otimizado para respostas em tempo real',
    icon: '⚡',
    color: '#f59e0b',
  },
  {
    id: '3',
    title: '🔒 Privacidade',
    description: 'Suas conversas são seguras e privadas',
    icon: '🔒',
    color: '#10b981',
  },
  {
    id: '4',
    title: '📱 Multiplataforma',
    description: 'Use em qualquer dispositivo, a qualquer momento',
    icon: '📱',
    color: '#ef4444',
  },
  {
    id: '5',
    title: '🌙 Modo Escuro',
    description: 'Interface adaptável para melhor experiência visual',
    icon: '🌙',
    color: '#8b5cf6',
  },
];

const FeatureCard = ({ 
  feature, 
  index, 
  expandedCard, 
  onCardPress,
  darkMode,
  setDarkMode
}: { 
  feature: Feature; 
  index: number;
  expandedCard: string | null;
  onCardPress: (id: string) => void;
  darkMode: boolean;
  setDarkMode: (value: boolean) => void;
}) => {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 600,
        delay: index * 150,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
    ]).start();
  }, [fadeAnim, slideAnim, index]);

  const handlePress = () => {
    Animated.sequence([
      Animated.spring(scaleAnim, {
        toValue: 0.95,
        useNativeDriver: true,
        speed: 20,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        useNativeDriver: true,
        speed: 20,
      }),
    ]).start();

    onCardPress(feature.id);
  };

  return (
    <Animated.View
      style={[
        styles.cardWrapper,
        {
          opacity: fadeAnim,
          transform: [{ translateY: slideAnim }],
        },
      ]}
    >
      <TouchableOpacity
        activeOpacity={0.9}
        onPress={handlePress}
      >
        <Animated.View
          style={[
            styles.card,
            { 
              borderLeftColor: feature.color,
              transform: [{ scale: scaleAnim }],
              backgroundColor: expandedCard === feature.id 
                ? (darkMode ? '#2d3748' : '#f9fafb')
                : (darkMode ? '#1f2937' : '#fff'),
            },
          ]}
        >
          <View style={styles.cardHeader}>
            <Text style={styles.cardIcon}>{feature.icon}</Text>
            <View style={styles.cardTitleContainer}>
              <Text style={[
                styles.cardTitle,
                darkMode && styles.cardTitleDark
              ]}>
                {feature.title}
              </Text>
              <Text style={[styles.cardBadge, { backgroundColor: feature.color + '20', color: feature.color }]}>
                Novo
              </Text>
            </View>
          </View>
          
          <Text style={[
            styles.cardDescription,
            darkMode && styles.cardDescriptionDark
          ]}>
            {feature.description}
          </Text>
          
          {expandedCard === feature.id && (
            <View style={styles.cardExpanded}>
              <View style={[styles.divider, { backgroundColor: feature.color + '40' }]} />
              <Text style={[
                styles.expandedText,
                darkMode && styles.expandedTextDark
              ]}>
                Esta funcionalidade está disponível para todos os usuários. 
                Comece a usar agora mesmo e explore todas as possibilidades!
              </Text>
              
              {feature.title === "🌙 Modo Escuro" && (
                <TouchableOpacity
                  style={[
                    styles.actionButton,
                    { backgroundColor: feature.color }
                  ]}
                  onPress={() => setDarkMode(!darkMode)}
                >
                  <Text style={styles.actionButtonText}>
                    {darkMode ? "Desativar" : "Ativar"}
                  </Text>
                </TouchableOpacity>
              )}
            </View>
          )}
        </Animated.View>
      </TouchableOpacity>
    </Animated.View>
  );
};

export default function Explore() {
  const [expandedCard, setExpandedCard] = useState<string | null>(null);
  const { darkMode, setDarkMode } = useTheme();

  const handleCardPress = (id: string) => {
    setExpandedCard(expandedCard === id ? null : id);
  };

  return (
    <>
      <StatusBar style={darkMode ? "light" : "dark"} />
      <ScrollView 
        style={[
          styles.container,
          darkMode && styles.containerDark
        ]} 
        showsVerticalScrollIndicator={false}
      >
        <View style={[
          styles.header,
          darkMode && styles.headerDark
        ]}>
          <Text style={[
            styles.headerTitle,
            darkMode && styles.headerTitleDark
          ]}>
            Explore
          </Text>
          <Text style={[
            styles.headerSubtitle,
            darkMode && styles.headerSubtitleDark
          ]}>
            Descubra todos os recursos disponíveis
          </Text>
        </View>

        <View style={styles.statsContainer}>
          <View style={[
            styles.statCard,
            darkMode && styles.statCardDark
          ]}>
            <Text style={styles.statNumber}>5+</Text>
            <Text style={[
              styles.statLabel,
              darkMode && styles.statLabelDark
            ]}>Funcionalidades Futuras</Text>
          </View>
          <View style={[
            styles.statCard,
            darkMode && styles.statCardDark
          ]}>
            <Text style={styles.statNumber}>2</Text>
            <Text style={[
              styles.statLabel,
              darkMode && styles.statLabelDark
            ]}>Modelos</Text>
          </View>
          <View style={[
            styles.statCard,
            darkMode && styles.statCardDark
          ]}>
            <Text style={styles.statNumber}>100%</Text>
            <Text style={[
              styles.statLabel,
              darkMode && styles.statLabelDark
            ]}>Gratuito</Text>
          </View>
        </View>

        <View style={styles.featuresContainer}>
          <Text style={[
            styles.sectionTitle,
            darkMode && styles.sectionTitleDark
          ]}>
            Recursos Principais
          </Text>
          {features.map((feature, index) => (
            <FeatureCard
              key={feature.id}
              feature={feature}
              index={index}
              expandedCard={expandedCard}
              onCardPress={handleCardPress}
              darkMode={darkMode}
              setDarkMode={setDarkMode}
            />
          ))}
        </View>

        <View style={styles.footer}>
          <Text style={[
            styles.footerText,
            darkMode && styles.footerTextDark
          ]}>
            Versão 1.0.0 atualizado em 15.03.2026 - versao beta, sujeito a mudanças.
          </Text>
        </View>
      </ScrollView>
    </>
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
    padding: 30,
    paddingTop: 60,
    backgroundColor: "#fff",
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 15,
    elevation: 3,
  },
  headerDark: {
    backgroundColor: "#1f2937",
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: "bold",
    color: "#1f2937",
    marginBottom: 8,
  },
  headerTitleDark: {
    color: "#f9fafb",
  },
  headerSubtitle: {
    fontSize: 16,
    color: "#6b7280",
    lineHeight: 22,
  },
  headerSubtitleDark: {
    color: "#9ca3af",
  },
  statsContainer: {
    flexDirection: "row",
    justifyContent: "space-around",
    padding: 20,
    marginTop: -20,
  },
  statCard: {
    backgroundColor: "#fff",
    padding: 15,
    borderRadius: 15,
    alignItems: "center",
    minWidth: 90,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 2,
  },
  statCardDark: {
    backgroundColor: "#1f2937",
  },
  statNumber: {
    fontSize: 20,
    fontWeight: "bold",
    color: "#6366f1",
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: "#6b7280",
  },
  statLabelDark: {
    color: "#9ca3af",
  },
  featuresContainer: {
    padding: 20,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: "600",
    color: "#1f2937",
    marginBottom: 15,
    marginLeft: 5,
  },
  sectionTitleDark: {
    color: "#f9fafb",
  },
  cardWrapper: {
    marginBottom: 15,
  },
  card: {
    borderRadius: 20,
    padding: 20,
    borderLeftWidth: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 12,
  },
  cardIcon: {
    fontSize: 32,
    marginRight: 12,
  },
  cardTitleContainer: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#1f2937",
  },
  cardTitleDark: {
    color: "#f9fafb",
  },
  cardBadge: {
    fontSize: 12,
    fontWeight: "600",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    overflow: "hidden",
  },
  cardDescription: {
    fontSize: 14,
    color: "#6b7280",
    lineHeight: 20,
  },
  cardDescriptionDark: {
    color: "#9ca3af",
  },
  cardExpanded: {
    marginTop: 15,
  },
  divider: {
    height: 1,
    marginVertical: 15,
  },
  expandedText: {
    fontSize: 14,
    color: "#4b5563",
    lineHeight: 20,
    marginBottom: 15,
  },
  expandedTextDark: {
    color: "#9ca3af",
  },
  actionButton: {
    padding: 12,
    borderRadius: 12,
    alignItems: "center",
  },
  actionButtonText: {
    color: "#fff",
    fontWeight: "600",
    fontSize: 14,
  },
  footer: {
    padding: 30,
    alignItems: "center",
  },
  footerText: {
    fontSize: 12,
    color: "#9ca3af",
  },
  footerTextDark: {
    color: "#6b7280",
  },
});