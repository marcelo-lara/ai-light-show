export default function Bar({ level, label, color }) {

  
  return (
    <div
      className="flex flex-col items-center transition-all duration-200"
      style={{ width: '20px' }}
    >
      {/* Energy Container */}
      <div
        className="flex items-end w-full bg-gray-800 rounded"
        style={{ height: '100px' }}
      >
        <div
          className="bg-green-500 w-full rounded-t"
          style={{
            height: `${level}%`,
            transition: 'height 0.2s',
          }}
        ></div>
      </div>

      {/* Label Box */}
      <div
        className="w-full text-xs text-white flex items-center justify-center mt-1"
        style={{
          backgroundColor: color || 'gray',
          height: '20px',
          minWidth: '15px',
        }}
      >
        {label}
      </div>
    </div>
  );
}
