import Head from 'next/head';
import Chat from '../components/Chat';

export default function Home() {
  return (
    <>
      <Head>
        <title>FitFinder Wardrobe Assistant</title>
      </Head>
      <main className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
        <Chat />
      </main>
    </>
  );
}
