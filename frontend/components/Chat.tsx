import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { chatWithAssistant } from '../services/api';
import { useRef } from 'react';

const chatSchema = z.object({
  prompt: z.string().min(1),
  image: z.any().optional(),
});

type ChatInputs = z.infer<typeof chatSchema>;

export default function Chat() {
  const { register, handleSubmit, formState: { errors } } = useForm<ChatInputs>({
    resolver: zodResolver(chatSchema),
  });
  const mutation = useMutation(chatWithAssistant);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const onSubmit: SubmitHandler<ChatInputs> = (data) => {
    const formData = new FormData();
    formData.append('prompt', data.prompt);
    if (data.image && data.image.length > 0) {
      formData.append('image', data.image[0]);
    }
    mutation.mutate(formData);
  };

  return (
    <div className="w-full max-w-xl mx-auto p-4 bg-white rounded shadow">
      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
        <textarea {...register('prompt')} placeholder="Type your prompt..." className="textarea textarea-bordered" />
        {errors.prompt && <span className="text-red-500">Prompt is required</span>}
        <input type="file" {...register('image')} ref={fileInputRef} />
        <button type="submit" className="btn btn-primary" disabled={mutation.isLoading}>
          {mutation.isLoading ? 'Sending...' : 'Send'}
        </button>
      </form>
      {mutation.data && (
        <div className="mt-4">
          <div className="font-bold">Assistant:</div>
          <div>{mutation.data.response_text}</div>
          {mutation.data.matching_outfits && (
            <ul className="mt-2 space-y-2">
              {mutation.data.matching_outfits.map((outfit: any) => (
                <li key={outfit.id} className="border p-2 rounded">
                  <img src={outfit.image_url} alt={outfit.description} className="w-24 h-24 object-cover rounded" />
                  <div>{outfit.description}</div>
                  <div className="text-xs text-gray-500">Tags: {outfit.tags.join(', ')}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
