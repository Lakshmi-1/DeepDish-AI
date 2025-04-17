import { useState, useEffect, useRef } from 'react';
import pizzaIcon from './assets/pizza.png';
import background from './assets/background.jpg';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowUp } from '@fortawesome/free-solid-svg-icons';
import { faSquare } from '@fortawesome/free-solid-svg-icons';

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

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
    if (loading) return;
    fetchQueryResult();
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  useEffect(() => {
    adjustTextareaHeight();
  }, [query]);

  const getMessageClass = (text) => {
    const lines = text.split('\n').length; 
    const t = Math.floor(text.length / 30); 
    return lines > 1 || t > 1 ? 'rounded-lg' : 'rounded-full'; 
  };

  return (
    <div className="flex flex-col min-h-screen">
      <div
        className="fixed top-0 left-0 w-full opacity-5 h-full bg-cover bg-center z-0"
        style={{ backgroundImage: `url(${background})` }}
      ></div>

      <div className="fixed flex items-center w-full p-4 text-3xl font-bold bg-green text-black rounded-b-md z-50">
        <img src={pizzaIcon} className="justify-center w-[30px] h-[30px] ml-2 mr-5" />
        DeepDish AI
      </div>
      <div className="flex-1 overflow-auto pt-[80px] pb-[120px] relative flex justify-center">
        <div className="w-full max-w-3xl px-4 space-y-4">
          {messages.map((msg, index) => (
            <div key={index} className={`flex items-center ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <p
                className={`px-4 py-2 ${getMessageClass(msg.text)} ${msg.sender === 'user' ? 'bg-purple text-white' : 'bg-gray-300 text-black'} break-words whitespace-pre-wrap max-w-[500px]`}
              >
                {msg.text}
              </p>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <span className="animate-bounce mx-1 text-2xl">.</span>
              <span className="animate-bounce mx-1 text-2xl delay-100">.</span>
              <span className="animate-bounce mx-1 text-2xl delay-200">.</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>
      <form
        onSubmit={handleSubmit}
        className="fixed bottom-0 w-full flex items-center bg-white justify-center px-4 pb-4 z-50"
      >
        <div className="w-full max-w-3xl flex gap-2">
          <div className="flex-1 outline bg-gray-200 rounded-lg p-2 flex">
            <textarea
              ref={textareaRef}
              value={query}
              onChange={handleQueryChange}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              className="w-full p-2 bg-transparent focus:outline-none resize-none"
              placeholder="Type your message..."
              rows="1"
            />
          </div>
          <div className="flex items-end">
            <button
              disabled={loading}
              type="submit"
              className={`w-[48px] h-[48px] flex items-center justify-center text-white rounded-full bg-black hover:bg-gray-500 cursor-pointer`}
            >
              <FontAwesomeIcon icon={loading ? faSquare : faArrowUp} />
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

export default App;
