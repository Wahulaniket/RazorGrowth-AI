'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, ShoppingBag } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { apiClient } from '@/lib/api/apiClient';
import { useCart } from '@/lib/contexts/CartContext';
import { toast } from 'sonner';

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  recommendations?: any[];
};

export function AIChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I am the RazorGrowth AI assistant. How can I help you shop today?',
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { addItem } = useCart();

  useEffect(() => {
    if (!sessionId) {
      setSessionId(Math.random().toString(36).substring(7));
    }
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sessionId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const { data, error } = await apiClient.POST('/api/v1/agent/chat', {
        body: {
          message: userMessage.content,
          session_id: sessionId,
        }
      });

      if (error) {
        throw new Error((error as any).detail || 'Failed to get response');
      }

      if (data) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.message || '',
          recommendations: data.recommendations || [],
        };
        setMessages((prev) => [...prev, assistantMessage]);
      }
    } catch (err: any) {
      toast.error(err.message || 'An error occurred while chatting with the AI.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddToCart = async (productId: string) => {
    try {
      await addItem(productId, 1);
      toast.success('Added to cart');
    } catch (err: any) {
      toast.error('Failed to add to cart: ' + (err.message || 'Unknown error'));
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50/50">
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className={`flex max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${msg.role === 'user' ? 'bg-primary text-white ml-3' : 'bg-blue-100 text-blue-600 mr-3'}`}>
                {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className="flex flex-col space-y-2">
                {msg.content && (
                  <div
                    className={`px-4 py-3 rounded-2xl ${
                      msg.role === 'user'
                        ? 'bg-primary text-primary-foreground rounded-tr-none'
                        : 'bg-white border text-gray-800 rounded-tl-none shadow-sm'
                    }`}
                  >
                    <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                  </div>
                )}
                
                {msg.recommendations && msg.recommendations.length > 0 && (
                  <div className="flex flex-col space-y-3 mt-2">
                    {msg.recommendations.map((product: any, idx: number) => (
                      <div key={idx} className="bg-white border rounded-xl p-4 shadow-sm flex gap-4 w-full max-w-sm">
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900">{product.name}</h4>
                          <p className="text-xs text-gray-500 mt-1 line-clamp-2">{product.description}</p>
                          <div className="mt-3 flex items-center justify-between">
                            <span className="font-bold text-lg text-gray-900">
                              {product.currency === 'INR' ? '₹' : product.currency} {product.price}
                            </span>
                            <Button size="sm" onClick={() => handleAddToCart(product.id)} className="h-8 rounded-full px-4">
                              Add to Cart
                            </Button>
                          </div>
                          {product.stock_quantity !== undefined && (
                            <p className={`text-xs mt-2 ${product.stock_quantity > 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {product.stock_quantity > 0 ? `In Stock (${product.stock_quantity})` : 'Out of Stock'}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="flex flex-row max-w-[85%]">
              <div className="flex-shrink-0 h-8 w-8 rounded-full bg-blue-100 text-blue-600 mr-3 flex items-center justify-center">
                <Bot size={16} />
              </div>
              <div className="px-4 py-3 rounded-2xl bg-white border text-gray-800 rounded-tl-none shadow-sm flex items-center">
                <Loader2 className="h-4 w-4 animate-spin text-gray-500 mr-2" />
                <span className="text-sm text-gray-500">Thinking...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-white border-t">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message... e.g. 'I need a laptop for coding'"
            className="flex-1 rounded-full px-6 focus-visible:ring-primary"
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading || !input.trim()} size="icon" className="rounded-full h-10 w-10 shrink-0">
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
