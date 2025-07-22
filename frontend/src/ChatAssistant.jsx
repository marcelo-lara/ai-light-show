import { useRef, useState } from 'preact/hooks';
import { useEffect } from 'react';
import { marked } from 'marked';

export default function ChatAssistant({ wsSend, lastResponse, contextProgress, llmStatus }) {
  const [message, setMessage] = useState("");
  const lastSentMessageRef = useRef("");
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
    // Add to chat with special styling for direct commands
    const isDirectCommand = message.trim().startsWith("#");
    setChat((prev) => [...prev, { 
      sender: 'user', 
      text: message,
      isDirectCommand
    }]);
    if (wsSend) {
      wsSend('userPrompt', { prompt: message });
    }
    lastSentMessageRef.current = message;
    setMessage("");
  };

  useEffect(() => {
    if (lastResponse) {
      // Only add lastResponse if streaming was never started (non-streaming response)
      if (!isStreaming && currentStreamingMessage === "") {
        // Check if the last message in chat is already this response
        setChat((prev) => {
          if (prev.length > 0 && prev[prev.length - 1].sender === 'assistant' && prev[prev.length - 1].text === lastResponse) {
            return prev; // Don't add duplicate
          }
          return [...prev, { sender: 'assistant', text: lastResponse }];
        });
      }
    }
  }, [lastResponse, isStreaming, currentStreamingMessage]);
  
  return (
    <div>
      <h2 className="text-lg mb-2 font-semibold">Assistant</h2>
      
      {/* LLM Status Indicator */}
      {llmStatus && llmStatus.length > 0 && (
        <div className="mb-3 p-2 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center gap-2">
          <div className="flex items-center gap-2">
            {llmStatus === "loading..." && (
              <div className="animate-spin w-4 h-4 border-2 border-yellow-500 border-t-transparent rounded-full"></div>
            )}
            {llmStatus === "connected..." && (
              <div className="w-4 h-4 bg-green-500 rounded-full animate-pulse"></div>
            )}
            {llmStatus === "thinking..." && (
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            )}
            {llmStatus === "error" && (
              <div className="w-4 h-4 bg-red-500 rounded-full">
                <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
            )}
            <span className="text-sm font-medium text-gray-700">
              {llmStatus === "loading..." && "Connecting to AI..."}
              {llmStatus === "connected..." && "Connected"}
              {llmStatus === "thinking..." && "AI is thinking..."}
              {llmStatus === "error" && "Connection error"}
              {!["loading...", "connected...", "thinking...", "error"].includes(llmStatus) && llmStatus}
            </span>
          </div>
        </div>
      )}
      
      {/* Context Analysis Progress Bar */}
      {contextProgress?.isRunning && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-800">Analyzing Context</span>
            <span className="text-sm text-blue-600">{contextProgress.progress}%</span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${contextProgress.progress}%` }}
            ></div>
          </div>
          <div className="mt-2 text-xs text-blue-700">
            {contextProgress.message || `Processing chunk ${contextProgress.current}/${contextProgress.total}`}
          </div>
        </div>
      )}
      
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
                ? (msg.isDirectCommand 
                   ? 'bg-purple-600 text-white self-end ml-auto text-right'
                   : 'bg-blue-600 text-white self-end ml-auto text-right')
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
              <div>
                {msg.isDirectCommand ? (
                  <strong>Direct Command:</strong>
                ) : null}
                <div>{msg.text}</div>
              </div>
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
          placeholder="Type a message or # command (e.g. #add flash to parcan at 1m23s duration 2b)"
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
            } else if (e.key === 'ArrowUp' && !e.shiftKey && !message) {
              // Recall last sent message if input is empty
              if (lastSentMessageRef.current) {
                setMessage(lastSentMessageRef.current);
                // Move cursor to end
                setTimeout(() => {
                  if (e.target.setSelectionRange) {
                    e.target.setSelectionRange(lastSentMessageRef.current.length, lastSentMessageRef.current.length);
                  }
                }, 0);
              }
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
