import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUser, faRobot } from '@fortawesome/free-solid-svg-icons';

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');

  const handleQueryChange = (e) => {
    setQuery(e.target.value);
  };

  const fetchQueryResult = async () => {
    if (!query) return;

    setLoading(true);
    setMessages((prev) => [...prev, { sender: 'user', text: query }]);
    setQuery('');

    try {
      const response = await fetch('http://127.0.0.1:5000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();
      if (data.result) {
        setMessages((prev) => [...prev, { sender: 'bot', text: data.result.result }]);
      } else {
        setMessages((prev) => [...prev, { sender: 'bot', text: 'No results found.' }]);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setMessages((prev) => [...prev, { sender: 'bot', text: 'An error occurred while fetching data.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchQueryResult();
  };

  return (
    <div className="flex flex-col justify-between min-h-screen bg-gradient-to-r from-mint-500 via-pink-500 to-red-500 p-4">
      <div className="flex flex-col space-y-4 overflow-auto max-h-[80vh] p-4 bg-white shadow-lg rounded-lg">
        {messages.map((msg, index) => (
          <div key={index} className={`flex items-center ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.sender === 'bot' && <FontAwesomeIcon icon={faRobot} className="text-green-500 mr-2" />}
            <p className={`p-2 rounded ${msg.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-300 text-black'}`}>{msg.text}</p>
            {msg.sender === 'user' && <FontAwesomeIcon icon={faUser} className="text-blue-500 ml-2" />}
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <span className="animate-bounce mx-1 text-2xl">.</span>
            <span className="animate-bounce mx-1 text-2xl delay-100">.</span>
            <span className="animate-bounce mx-1 text-2xl delay-200">.</span>
          </div>
        )}
      </div>
      <form onSubmit={handleSubmit} className="flex p-4 bg-white shadow-lg rounded-lg mt-4">
        <input
          type="text"
          value={query}
          onChange={handleQueryChange}
          className="flex-1 p-2 border rounded"
          placeholder="Type your message..."
        />
        <button type="submit" className="ml-4 p-2 bg-blue-500 text-white rounded">
          Send
        </button>
      </form>
    </div>
  );
}

export default App;