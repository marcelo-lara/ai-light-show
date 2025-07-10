import { useRef, useState } from 'preact/hooks';
import { useEffect } from 'react';
import { marked } from 'marked';

export default function ChatAssistant({ wsSend, lastResponse }) {
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState("");
  const chatContainerRef = useRef(null);

  // Configure marked for safer HTML output
  marked.setOptions({
    breaks: true, // Convert line breaks to <br>
    gfm: true,    // GitHub flavored markdown
  });

  // Function to render markdown safely
  const renderMarkdown = (text) => {
    try {
      const html = marked.parse(text);
      return { __html: html };
    } catch (error) {
      console.error('Markdown parsing error:', error);
      return { __html: text }; // Fallback to plain text
    }
  };

  // Function to scroll to bottom
  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  };

  // Expose streaming handlers globally
  window._chatAssistantStartStreaming = () => {
    setIsStreaming(true);
    setCurrentStreamingMessage("");
  };
  
  window._chatAssistantAppendChunk = (chunk) => {
    setCurrentStreamingMessage(prev => prev + chunk);
  };
  
  window._chatAssistantEndStreaming = () => {
    setChat(prev => [...prev, { sender: 'assistant', text: currentStreamingMessage }]);
    setCurrentStreamingMessage("");
    setIsStreaming(false);
  };

  // Auto-scroll when chat updates
  useEffect(() => {
    scrollToBottom();
  }, [chat, currentStreamingMessage]);

  const sendMessage = () => {
    if (!message.trim()) return;
    setChat((prev) => [...prev, { sender: 'user', text: message }]);
    if (wsSend) {
      wsSend('userPrompt', { prompt: message });
    }
    setMessage("");
  };

  useEffect(() => {
    if (lastResponse) {
      setChat((prev) => [...prev, { sender: 'assistant', text: lastResponse }]);
    }
  }, [lastResponse]);
  
  return (
    <div>
      <h2 className="text-lg mb-2 font-semibold">Assistant</h2>
      <div className="flex flex-col gap-2 mb-4 max-h-60 overflow-y-auto" ref={chatContainerRef}>
        {chat.length === 0 && (
          <p className="text-sm text-gray-400">No messages yet.</p>
        )}
        {chat.map((msg, idx) => (
          <div
            key={idx}
            className={
              'max-w-[75%] px-4 py-2 rounded-lg text-sm ' +
              (msg.sender === 'user'
                ? 'bg-blue-600 text-white self-end ml-auto text-right'
                : 'bg-gray-200 text-gray-900 self-start mr-auto text-left')
            }
            style={{ alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}
          >
            {msg.sender === 'assistant' ? (
              <div 
                className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-strong:text-gray-900 prose-code:text-gray-800 prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded prose-pre:bg-gray-100 prose-pre:text-gray-800"
                dangerouslySetInnerHTML={renderMarkdown(msg.text)}
              />
            ) : (
              msg.text
            )}
          </div>
        ))}
        {isStreaming && (
          <div
            className="max-w-[75%] px-4 py-2 rounded-lg text-sm bg-gray-200 text-gray-900 self-start mr-auto text-left"
            style={{ alignSelf: 'flex-start' }}
          >
            <div 
              className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-strong:text-gray-900 prose-code:text-gray-800 prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded prose-pre:bg-gray-100 prose-pre:text-gray-800"
              dangerouslySetInnerHTML={renderMarkdown(currentStreamingMessage)}
            />
            <span className="animate-pulse">|</span>
          </div>
        )}
      </div>
      <div className="mt-4 flex gap-2 items-end">
        <textarea
          className="flex-1 min-h-[2.5rem] max-h-32 p-2 bg-gray-800 text-white rounded resize-none"
          placeholder="Type your message here..."
          rows="1"
          value={message}
          onInput={(e) => {
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px';
            setMessage(e.target.value);
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
              setMessage("");
            }
          }}
        ></textarea>
        <button
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded whitespace-nowrap"
          onClick={sendMessage}
        >
          Send ➤
        </button>
      </div>
    </div>
  );
}
