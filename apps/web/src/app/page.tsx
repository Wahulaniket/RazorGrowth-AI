import { Navbar } from '@/components/navbar';
import { AIChat } from '@/components/ai-chat';

export default function Home() {
  return (
    <div className="flex flex-col h-full min-h-screen bg-gray-50">
      <Navbar />
      <main className="flex-1 flex flex-col max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8 h-full">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl">
            Conversational Shopping
          </h1>
          <p className="mt-4 text-xl text-gray-500">
            Ask our AI agent for recommendations, search the catalog, and checkout seamlessly.
          </p>
        </div>
        
        <div className="flex-1 flex justify-center w-full min-h-[600px] mb-8">
          <div className="w-full max-w-4xl bg-white border rounded-xl shadow-lg flex flex-col overflow-hidden">
            <AIChat />
          </div>
        </div>
      </main>
    </div>
  );
}
