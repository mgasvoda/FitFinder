import React from "react";

export interface ChatBubbleProps {
  message: string;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message }) => (
  <div className="flex items-start">
    <span className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-purple-100 text-2xl mr-3">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <circle cx="12" cy="12" r="10" stroke="#6D4C7E" strokeWidth="2"/>
        <circle cx="8" cy="10" r="1.5" fill="#6D4C7E"/>
        <circle cx="16" cy="10" r="1.5" fill="#6D4C7E"/>
        <path d="M8 15C8.5 16.5 10 18 12 18C14 18 15.5 16.5 16 15" stroke="#6D4C7E" strokeWidth="2" strokeLinecap="round"/>
      </svg>
    </span>
    <div className="bg-white rounded-2xl px-6 py-4 shadow-md text-lg text-purple-900 border border-purple-100">
      {message}
    </div>
  </div>
);
