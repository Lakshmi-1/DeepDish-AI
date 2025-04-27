import { useState, useEffect, useRef } from 'react';
import pizzaIcon from './assets/pizza.png';
import background from './assets/background.jpg';
import personIcon from './assets/person.png';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faArrowUp, faSquare } from '@fortawesome/free-solid-svg-icons';
import { motion, AnimatePresence } from 'framer-motion';

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [initial, setInitial] = useState(true);
  const [showPopup, setShowPopup] = useState(false);
  const [namePopupInput, setNamePopupInput] = useState('');
  const [allergiesPopupInput, setAllergiesPopupInput] = useState('');
  const [location, setLocation] = useState(null);
  const [locationError, setLocationError] = useState(false);
  const [city, setCity] = useState('');




  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const handleQueryChange = (e) => setQuery(e.target.value);

  const fetchQueryResult = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setMessages((prev) => [...prev, { sender: 'user', text: query }]);
    setQuery('');
    setInitial(false);

    try {
      const response = await fetch('http://127.0.0.1:5000/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
  useEffect(() => {
    const stopWatching = getLocation();
    return () => {
      if (stopWatching) stopWatching();
    };
  }, []);



  const getMessageClass = (text) => {
    const lines = text.split('\n').length;
    const t = Math.floor(text.length / 30);
    return lines > 1 || t > 1 ? 'rounded-lg' : 'rounded-full';
  };

const getLocation = () => {
  setLocation(null);
  setLocationError(false);
  if (navigator.geolocation) {
    const watchId = navigator.geolocation.watchPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        setLocation({ latitude: lat, longitude: lon });
        setLocationError(false);

        // Fetch city name
        try {
          const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
          const data = await response.json();
          if (data.address) {
            const cityName = data.address.city || data.address.town || data.address.village || data.address.state;
            setCity(cityName);
          }
        } catch (error) {
          console.error('Error fetching city name:', error);
        }
      },
      (error) => {
        console.error('Error getting location:', error);
        setLocationError(true);
      }
    );

    // Cleanup watcher if needed
    return () => navigator.geolocation.clearWatch(watchId);
  } else {
    console.error('Geolocation not supported');
    setLocationError(true);
  }
};



  return (
    <div className="flex flex-col min-h-screen relative">

      <div
        className="fixed top-0 left-0 w-full opacity-5 h-full bg-cover bg-center z-0"
        style={{ backgroundImage: `url(${background})` }}
      ></div>


      <div className="fixed flex items-center justify-between w-full p-4 text-3xl font-bold bg-green text-black rounded-b-md z-50">
        <div className="flex items-center">
            <img src={pizzaIcon} className="w-[30px] h-[30px] ml-2 mr-5" />
            DeepDish AI
        </div>
            <button
                onClick={() => setShowPopup(true)}
                className="flex items-center justify-center w-[40px] h-[40px] mr-2 bg-white rounded-full shadow-md hover:bg-gray-200"
            >
                <img src={personIcon} className="w-[25px] h-[25px]" alt="Profile" />
            </button>
      </div>

      {showPopup && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/70 z-50 backdrop-blur">
            <div className="bg-white p-6 rounded-lg shadow-lg">
                <h2 className="text-2xl font-bold mb-4">Profile</h2>

               <p className= "text-black mb-4">Personalize Name: </p>
                <input
                    type="text"
                    value={namePopupInput}
                    onChange={(e) => setNamePopupInput(e.target.value)}
                    placeholder="Enter something..."
                    className="w-full p-2 border rounded mb-4"
                />


                <p className= "text-black mb-4">Enter Allergies - Please separate by comma: </p>
                <input
                    type="text"
                    value={allergiesPopupInput}
                    onChange={(e) => setAllergiesPopupInput(e.target.value)}
                    placeholder="Enter something..."
                    className="w-full p-2 border rounded mb-4"
                />

                <div className="text-sm text-black ml-5">
                  {location ? (
                    <div className="flex items-center space-x-2">
                      <span>📍</span>
                      {city ? (
                        <span>{city}</span>
                      ) : (
                        <span>Lat: {location.latitude.toFixed(2)}, Lon: {location.longitude.toFixed(2)}</span>
                      )}
                    </div>
                  ) : locationError ? (
                    <button
                      onClick={getLocation}
                      className="px-2 py-1 bg-white text-green-700 rounded shadow hover:bg-gray-200 text-xs"
                    >
                      Enable Location
                    </button>
                  ) : (
                    <p>Loading location...</p>
                  )}
                </div>




                <button
                    onClick={() => setShowPopup(false)}
                    className="mt-4 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                >
                    Close
                </button>
            </div>
        </div>
      )}




 
      <div className="flex-1 overflow-auto pt-[80px] pb-[120px] relative flex justify-center z-10">
        <div className="w-full max-w-3xl px-4 space-y-4">
          {messages.map((msg, index) => (
            <div key={index} className={`flex items-center ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <p
                className={`px-4 py-2 ${getMessageClass(msg.text)} ${msg.sender === 'user' ? 'bg-purple text-white' : 'bg-gray-300 text-black'} break-words whitespace-pre-wrap max-w-[500px] transition-all duration-300`}
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

      <AnimatePresence>
        {initial ? (
          <motion.div
            key="initial-input"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            transition={{ duration: 0.5 }}
            className="absolute inset-0 flex flex-col items-center justify-center bg-white/70 z-50 backdrop-blur"
          >
            <img src={pizzaIcon} className="w-[100px] h-[100px] mb-4" />
            <h1 className="text-4xl font-bold mb-4 text-black">Welcome to DeepDish AI!</h1>
            <h2 className="text-2xl font-semibold mb-4 text-black">How can I help you?</h2>
            <form onSubmit={handleSubmit} className="w-full max-w-xl px-4">
              <div className="flex gap-2">
                <div className="flex-1 bg-gray-200 rounded-lg p-2 flex">
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
                    className="w-[48px] h-[48px] flex items-center justify-center text-white rounded-full bg-black hover:bg-gray-500 transition-all"
                  >
                    <FontAwesomeIcon icon={loading ? faSquare : faArrowUp} />
                  </button>
                </div>
              </div>
            </form>
          </motion.div>
        ) : (
          <motion.form
            key="bottom-input"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 30 }}
            transition={{ duration: 0.5 }}
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
                  className="w-[48px] h-[48px] flex items-center justify-center text-white rounded-full bg-black hover:bg-gray-500 transition-all"
                >
                  <FontAwesomeIcon icon={loading ? faSquare : faArrowUp} />
                </button>
              </div>
            </div>
          </motion.form>
        )}
      </AnimatePresence>
    </div>
  );
}

export default App;