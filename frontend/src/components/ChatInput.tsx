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
      <div className="relative bg-chat-input rounded-2xl border border-chat-border shadow-lg">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe your symptoms..."
          className="w-full px-4 py-3 pr-12 bg-transparent text-white placeholder-gray-400 border-none outline-none resize-none rounded-2xl min-h-[50px] max-h-[200px] overflow-y-auto"
          rows={1}
          disabled={disabled || isLoading}
        />
        
        {/* Send Button */}
        <button
          type="submit"
          disabled={disabled || !message.trim() || isLoading}
          className={`absolute right-3 bottom-3 w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-200 ${
            message.trim() && !isLoading
              ? 'bg-blue-600 hover:bg-blue-700 text-white cursor-pointer'
              : 'bg-gray-600 text-gray-400 cursor-not-allowed'
          }`}
        >
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <i className="fas fa-paper-plane text-sm"></i>
          )}
        </button>
      </div>
      
      {/* Helper Text */}
      <div className="mt-2 text-xs text-gray-400 text-center">
        Press Enter to send, Shift + Enter for new line
      </div>
    </form>
  );
};

export default ChatInput; 