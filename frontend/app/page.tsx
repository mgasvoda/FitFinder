"use client";
import { useState } from 'react';
import { FitFinderHeader, WardrobeIllustrations, ChatBubble, BackgroundConfetti } from '../components';
import { chatWithAssistant } from '../services/api';
import { ArrowRight } from 'lucide-react';

export default function Home() {
  const [messages, setMessages] = useState<Array<{type: 'user' | 'assistant', content: string}>>([
    { type: 'assistant', content: "How can I assist you with your wardrobe?" }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;
    
    // Add user message immediately
    const userMessage = inputValue;
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setInputValue('');
    
    // Set loading state
    setIsLoading(true);
    
    try {
      const response = await chatWithAssistant(userMessage);
      
      // Add assistant message
      setMessages(prev => [...prev, { type: 'assistant', content: response.response_text }]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { type: 'assistant', content: 'Sorry, there was an error processing your request.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden">
      <BackgroundConfetti />
      <div className="w-full max-w-md mx-auto p-6 rounded-3xl shadow-lg bg-white/90 backdrop-blur-sm relative z-10">
        <FitFinderHeader />
        <WardrobeIllustrations />
        
        <div className="my-6 space-y-4 max-h-[40vh] overflow-y-auto">
          {messages.map((message, index) => (
            <div key={index} className="mb-4">
              {message.type === 'assistant' ? (
                <ChatBubble message={message.content} />
              ) : (
                <div className="bg-blue-100 p-3 rounded-lg ml-auto max-w-[80%] text-right">
                  <div className="font-bold text-xs mb-1 text-blue-800">You</div>
                  <div className="text-blue-900">{message.content}</div>
                </div>
              )}
            </div>
          ))}
        </div>
        
        <form onSubmit={handleSubmit} className="flex items-center bg-white rounded-full px-4 py-2 shadow-md border border-gray-200 gap-2 w-full mt-4">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            className="flex-1 outline-none bg-transparent text-gray-700 text-base placeholder-gray-400"
            placeholder="Message"
            disabled={isLoading}
          />
          <button 
            type="submit" 
            className="ml-2 p-2 rounded-full bg-pink-100 hover:bg-pink-200 transition" 
            disabled={isLoading || !inputValue.trim()}
          >
            {isLoading ? (
              <span className="inline-block w-5 h-5 border-2 border-purple-700 border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <ArrowRight className="w-5 h-5 text-purple-900" />
            )}
          </button>
        </form>
      </div>
    </main>
  );
}
