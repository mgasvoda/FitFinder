"use client";
import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { chatWithAssistant } from '../services/api';
import { useRef, useState } from 'react';

const chatSchema = z.object({
  prompt: z.string().min(1),
  image: z.any().optional(),
});

type ChatInputs = z.infer<typeof chatSchema>;

export default function Chat() {
  const [messages, setMessages] = useState<Array<{type: 'user' | 'assistant', content: string}>>([]);
  const { register, handleSubmit, reset, formState: { errors } } = useForm<ChatInputs>({
    resolver: zodResolver(chatSchema),
  });
  
  const mutation = useMutation({
    mutationFn: chatWithAssistant,
    onSuccess: (data) => {
      console.log('Mutation success, received data:', data);
      setMessages(prev => [...prev, { type: 'assistant', content: data.response_text }]);
      reset();
    },
    onError: (error) => {
      console.error('Mutation error:', error);
    }
  });

  const onSubmit: SubmitHandler<ChatInputs> = (data) => {
    console.log('Form submitted with data:', data);
    // Add user message to the chat
    setMessages(prev => [...prev, { type: 'user', content: data.prompt }]);
    // Send to backend
    mutation.mutate(data.prompt);
  };

  return (
    <div className="w-full max-w-xl mx-auto p-4 bg-white rounded shadow">
      <div className="mb-4 h-64 overflow-y-auto border border-gray-200 rounded p-3">
        {messages.length === 0 ? (
          <div className="text-gray-400 text-center mt-20">No messages yet. Start a conversation!</div>
        ) : (
          messages.map((msg, idx) => (
            <div key={idx} className={`mb-2 p-2 rounded ${msg.type === 'user' ? 'bg-blue-100 ml-auto max-w-[80%]' : 'bg-gray-100 mr-auto max-w-[80%]'}`}>
              {msg.content}
            </div>
          ))
        )}
      </div>
      
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <textarea 
          {...register('prompt')} 
          placeholder="Type your prompt..." 
          className="textarea textarea-bordered" 
        />
        {errors.prompt && <span className="text-red-500">Prompt is required</span>}
        <button 
          type="submit" 
          className="btn btn-primary" 
          disabled={mutation.isLoading}
        >
          {mutation.isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
      
      {mutation.isError && (
        <div className="mt-2 text-red-500">
          Error: {mutation.error instanceof Error ? mutation.error.message : 'Unknown error'}
        </div>
      )}
    </div>
  );
}
