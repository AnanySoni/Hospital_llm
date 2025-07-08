import React, { useState, useRef, useEffect } from 'react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  disabled: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading, disabled }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [message]);

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="relative bg-gray-800 rounded-2xl border border-gray-600 shadow-lg ring-1 ring-gray-600/20">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe your symptoms..."
          className="w-full px-3 py-2 pr-10 bg-transparent text-white placeholder-gray-400 border-none outline-none resize-none rounded-2xl min-h-[40px] max-h-[120px] overflow-y-auto focus:ring-2 focus:ring-blue-500/50 transition-all text-sm"
          rows={1}
          disabled={disabled || isLoading}
        />
        
        {/* Send Button */}
        <button
          type="submit"
          disabled={disabled || !message.trim() || isLoading}
          className={`absolute right-2 bottom-2 w-7 h-7 rounded-lg flex items-center justify-center transition-all duration-200 ${
            message.trim() && !isLoading
              ? 'bg-blue-600 hover:bg-blue-700 text-white cursor-pointer shadow-md'
              : 'bg-gray-600 text-gray-400 cursor-not-allowed'
          }`}
        >
          {isLoading ? (
            <div className="w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <i className="fas fa-paper-plane text-xs"></i>
          )}
        </button>
      </div>
      
      {/* Helper Text */}
      <div className="mt-1 text-xs text-gray-500 text-center">
        Press Enter to send, Shift + Enter for new line
      </div>
    </form>
  );
};

export default ChatInput; 