import { useForm, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { uploadItem } from '../services/api';

const uploadSchema = z.object({
  image: z.any(),
});

type UploadInputs = z.infer<typeof uploadSchema>;

export function UploadForm() {
  const { register, handleSubmit, formState: { errors } } = useForm<UploadInputs>({
    resolver: zodResolver(uploadSchema),
  });

  const mutation = useMutation(uploadItem);

  const onSubmit: SubmitHandler<UploadInputs> = (data) => {
    const formData = new FormData();
    formData.append('image', data.image[0]);
    mutation.mutate(formData);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
      <input type="file" {...register('image')} />
      {errors.image && <span className="text-red-500">Image is required</span>}
      <button type="submit" className="btn btn-primary">Upload</button>
    </form>
  );
}
