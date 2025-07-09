import { useState } from 'preact/hooks';

export default function ChatAssistant() {
  const [message, setMessage] = useState("");
  // Placeholder for chat response, can be replaced with state/props
  const chatResponse = "chat response placeholder";

  return (
    <div>
      <h2 className="text-lg mb-2 font-semibold">Assistant</h2>
      <div className="text-sm text-gray-400">
        <p>{chatResponse}</p>
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
        ></textarea>
        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded whitespace-nowrap">
          Send ➤
        </button>
      </div>
    </div>
  );
}
