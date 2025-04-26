"use client";
import React, { useRef, useState, useEffect } from "react";
import { Paperclip, ArrowRight } from "lucide-react";
import { useForm, SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { chatWithAssistant } from "../services/api";

const chatSchema = z.object({
  prompt: z.string().min(1, "Message is required"),
  image: z.any().optional(),
});
type ChatInputs = z.infer<typeof chatSchema>;

export const MessageInput: React.FC<{
  onMessageSent?: (message: string, response: any) => void
}> = ({ onMessageSent }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [currentPrompt, setCurrentPrompt] = useState<string>("");
  
  const { register, handleSubmit, reset, formState: { errors } } = useForm<ChatInputs>({
    resolver: zodResolver(chatSchema),
  });
  
  const mutation = useMutation({
    mutationFn: chatWithAssistant,
    onSuccess: (data) => {
      console.log('MessageInput: Chat response received:', data);
      if (onMessageSent && currentPrompt) {
        onMessageSent(currentPrompt, data);
        setCurrentPrompt(""); // Clear the stored prompt after sending
      }
      reset();
    },
    onError: (error) => {
      console.error('MessageInput: Error in chat mutation:', error);
    }
  });

  const onSubmit: SubmitHandler<ChatInputs> = (data) => {
    console.log('MessageInput: Submitting form with data:', data);
    const prompt = data.prompt;
    setCurrentPrompt(prompt); // Store the current prompt for use in onSuccess
    
    // For now, only send prompt (extend for image if backend supports)
    mutation.mutate(prompt);
  };

  const handlePaperclipClick = (e: React.MouseEvent) => {
    e.preventDefault();
    fileInputRef.current?.click();
  };

  // Debug logging for render cycles
  useEffect(() => {
    console.log('MessageInput: Component rendered/updated');
  }, []);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex items-center bg-white rounded-full px-4 py-2 shadow border border-gray-200 gap-2 w-full">
      <button type="button" onClick={handlePaperclipClick} className="focus:outline-none">
        <Paperclip className="w-5 h-5 text-gray-400 mr-2" aria-label="Attach" />
      </button>
      <input
        type="file"
        {...register("image")}
        ref={fileInputRef}
        className="hidden"
      />
      <input
        type="text"
        {...register("prompt")}
        className="flex-1 outline-none bg-transparent text-gray-700 text-base placeholder-gray-400"
        placeholder="Message"
        aria-label="Message"
        disabled={mutation.isLoading}
      />
      <button 
        type="submit" 
        className="ml-2 p-2 rounded-full bg-yellow-200 hover:bg-yellow-300 transition" 
        disabled={mutation.isLoading}
      >
        {mutation.isLoading ? (
          <span className="inline-block w-5 h-5 border-2 border-gray-700 border-t-transparent rounded-full animate-spin"></span>
        ) : (
          <ArrowRight className="w-5 h-5 text-gray-700" />
        )}
      </button>
      
      {mutation.isError && (
        <div className="absolute bottom-full mb-2 p-2 bg-red-100 text-red-700 rounded text-sm">
          Error: {mutation.error instanceof Error ? mutation.error.message : 'Unknown error'}
        </div>
      )}
    </form>
  );
};
