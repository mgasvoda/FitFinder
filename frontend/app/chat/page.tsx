"use client";
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { chatWithAssistant } from '../../services/api';

export default function ChatPage() {
  const [messages, setMessages] = useState<Array<{type: 'user' | 'assistant', content: string}>>([]);
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
      console.log('Sending message:', userMessage);
      const response = await chatWithAssistant(userMessage);
      console.log('Received response:', response);
      
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
    <main className="min-h-screen flex flex-col bg-pink-50">
      <div className="flex-1 max-w-2xl w-full mx-auto p-4 flex flex-col">
        <div className="text-2xl font-bold mb-4 text-center">FitFinder Chat</div>
        
        {/* Messages display */}
        <div className="flex-1 overflow-y-auto mb-4 p-4 bg-white rounded-lg shadow h-[60vh]">
          {messages.length === 0 ? (
            <div className="text-gray-400 text-center py-10">
              No messages yet. Ask about your wardrobe or outfit suggestions!
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div 
                  key={index} 
                  className={`p-3 rounded-lg max-w-[80%] ${
                    message.type === 'user' 
                      ? 'bg-blue-100 ml-auto text-right' 
                      : 'bg-gray-100'
                  }`}
                >
                  <div className="font-bold text-xs mb-1">
                    {message.type === 'user' ? 'You' : 'Assistant'}
                  </div>
                  <div>{message.content}</div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Input form */}
        <form onSubmit={handleSubmit} className="flex items-center bg-white rounded-full px-4 py-2 shadow border border-gray-200 gap-2 w-full">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            className="flex-1 outline-none bg-transparent text-gray-700 text-base placeholder-gray-400"
            placeholder="Type your message..."
            disabled={isLoading}
          />
          <button 
            type="submit" 
            className="ml-2 p-2 rounded-full bg-yellow-200 hover:bg-yellow-300 transition" 
            disabled={isLoading || !inputValue.trim()}
          >
            {isLoading ? (
              <span className="inline-block w-5 h-5 border-2 border-gray-700 border-t-transparent rounded-full animate-spin"></span>
            ) : (
              <span>→</span>
            )}
          </button>
        </form>
      </div>
    </main>
  );
}
