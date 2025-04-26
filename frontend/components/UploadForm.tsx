import React from "react";
import { useForm, SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { uploadItem } from "../services/api";

const uploadSchema = z.object({
  image: z.any().optional(),
  description: z.string().min(1, "Description is required"),
});

type UploadInputs = z.infer<typeof uploadSchema>;

export const UploadForm: React.FC = () => {
  const { register, handleSubmit, formState: { errors } } = useForm<UploadInputs>({
    resolver: zodResolver(uploadSchema),
  });

  const onSubmit: SubmitHandler<UploadInputs> = async (data) => {
    const formData = new FormData();
    if (data.image && data.image[0]) {
      formData.append("image", data.image[0]);
    }
    formData.append("description", data.description);
    await uploadItem(formData);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4 w-full max-w-md mx-auto bg-white p-6 rounded-2xl shadow">
      <input type="file" {...register("image")} />
      <input type="text" {...register("description")}
        placeholder="Describe your item..."
        className="input input-bordered" />
      {errors.description && <span className="text-red-500">{errors.description.message}</span>}
      <button type="submit" className="btn btn-primary">Upload</button>
    </form>
  );
};
