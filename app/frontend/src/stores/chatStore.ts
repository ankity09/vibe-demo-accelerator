import { create } from 'zustand'
import type { ActionCardData, ChatMessage } from '@/types'

interface ChatState {
  messages: ChatMessage[]
  isStreaming: boolean
  currentThinking: string
  currentResponse: string
  currentToolCalls: string[]
  currentActionCards: ActionCardData[]
  currentSuggestedActions: string[]

  addMessage: (msg: ChatMessage) => void
  setStreaming: (val: boolean) => void
  appendThinking: (text: string) => void
  appendResponse: (text: string) => void
  addToolCall: (tool: string) => void
  addActionCard: (card: ActionCardData) => void
  setSuggestedActions: (actions: string[]) => void
  finishResponse: () => void
  clearHistory: () => void
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isStreaming: false,
  currentThinking: '',
  currentResponse: '',
  currentToolCalls: [],
  currentActionCards: [],
  currentSuggestedActions: [],

  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setStreaming: (val) => set({ isStreaming: val }),
  appendThinking: (text) => set((s) => ({ currentThinking: s.currentThinking + text })),
  appendResponse: (text) => set((s) => ({ currentResponse: s.currentResponse + text })),
  addToolCall: (tool) => set((s) => ({ currentToolCalls: [...s.currentToolCalls, tool] })),
  addActionCard: (card) => set((s) => ({ currentActionCards: [...s.currentActionCards, card] })),
  setSuggestedActions: (actions) => set({ currentSuggestedActions: actions }),

  finishResponse: () => {
    const state = get()
    const assistantMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: state.currentResponse,
      thinking: state.currentThinking || undefined,
      toolCalls: state.currentToolCalls.length ? state.currentToolCalls : undefined,
      actionCards: state.currentActionCards.length ? state.currentActionCards : undefined,
      suggestedActions: state.currentSuggestedActions.length ? state.currentSuggestedActions : undefined,
      timestamp: new Date(),
    }
    set({
      messages: [...state.messages, assistantMsg],
      currentThinking: '',
      currentResponse: '',
      currentToolCalls: [],
      currentActionCards: [],
      currentSuggestedActions: [],
      isStreaming: false,
    })
  },

  clearHistory: () => set({
    messages: [],
    currentThinking: '',
    currentResponse: '',
    currentToolCalls: [],
    currentActionCards: [],
    currentSuggestedActions: [],
  }),
}))
