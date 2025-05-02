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
  const [fullBotResponse, setFullBotResponse] = useState('');
  const [visibleBotResponse, setVisibleBotResponse] = useState('');
  const [locationEnabled, setLocationEnabled] = useState(true);

  const messagesEndRef = useRef(null);
  const popupRef = useRef();
  const textareaRef = useRef();
  const textareaRefBottom = useRef();

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (event.button !== 2 && popupRef.current && !popupRef.current.contains(event.target)) {
        setShowPopup(false);
      }
    };

    if (showPopup) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showPopup]);

  useEffect(() => {
    const handleClick = (event) => {
      const inputForm = document.getElementById('init_query_form');
      if (event.button !== 2 && initial && inputForm && !inputForm.contains(event.target)) {
        setInitial(false);
      }
    };
  
    if (initial) {
      document.addEventListener('mousedown', handleClick);
    }
  
    return () => {
      document.removeEventListener('mousedown', handleClick);
    };
  }, [initial]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

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
        body: JSON.stringify({
           query,
           allergies: allergiesPopupInput
          .split(',')
          .map(item => item.trim())
          .filter(item => item.length > 0),
          city: city,
          name: namePopupInput
          }),
      });

      const data = await response.json();
      if (data.result) {
        const fullText = data.result.result;
        setFullBotResponse(fullText);
        setVisibleBotResponse('');
        revealBotResponse(fullText);
      } else {
        setMessages((prev) => [...prev, { sender: 'bot', text: 'No results found.' }]);
        setLoading(false)
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setMessages((prev) => [...prev, { sender: 'bot', text: 'An error occurred while fetching data.' }]);
      setLoading(false)
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (loading) return;
    fetchQueryResult();
    resetTextareaHeight();
  };

  const resetTextareaHeight = () => {
    textareaRefBottom.current.style.height = 'auto';
    textareaRefBottom.current.style.height = `${textareaRef.current.scrollHeight}px`;
  };

  const handleTextareaInput = () => {
    textareaRef.current.style.height = 'auto';  
    textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 100)}px`;
  };

  const handleTextareaInputBottom = () => {
    textareaRefBottom.current.style.height = 'auto';
    textareaRefBottom.current.style.height = `${Math.min(textareaRefBottom.current.scrollHeight, 150)}px`;
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (locationEnabled) {
      getLocation();
    } else {
      setLocation(null);
      setCity('');
    }
  }, [locationEnabled]);

  useEffect(() => {
  if (!navigator.permissions) return;

  navigator.permissions.query({ name: 'geolocation' }).then((permissionStatus) => {
    permissionStatus.onchange = () => {
      if (permissionStatus.state === 'granted') {
        getLocation();
      }
    };
  });
}, []);


  const getMessageClass = (text) => {
    const lines = text.split('\n').length;
    const t = Math.floor(text.length / 30);
    return lines > 1 || t > 1 ? 'rounded-lg' : 'rounded-full';
  };

  const revealBotResponse = (text) => {
    const words = text.split(' ');
    let index = 0;

    const reveal = () => {
      const chunkSize = Math.floor(Math.random() * 4) + 1;
      const nextChunk = words.slice(index, index + chunkSize).join(' ');
      setVisibleBotResponse(prev => prev ? `${prev} ${nextChunk}` : nextChunk);
      index += chunkSize;

      if (index >= words.length) {
        clearInterval(timer);
        setMessages(prev => [...prev, { sender: 'bot', text }]);
        setVisibleBotResponse('');
        setLoading(false);
      }
    };

    const timer = setInterval(reveal, 200);
  };

  const getLocation = () => {
    if (!locationEnabled || !navigator.geolocation) return;
  
    const watchId = navigator.geolocation.watchPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        setLocation({ latitude: lat, longitude: lon });
        setLocationError(false);
  
        try {
          const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
          const data = await response.json();
          const cityName = data.address?.city || data.address?.town || data.address?.village || data.address?.state;
          setCity(cityName);
          
        } catch (error) {
          console.error('Error fetching city name:', error);
        }
      },
      (error) => {
        console.error('Error getting location:', error);
        setLocationError(true);
      }
    );
  
    return () => navigator.geolocation.clearWatch(watchId);
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
        <div className="fixed inset-0 flex flex-col items-center justify-center bg-white/70 z-70 backdrop-blur">
          <div ref={popupRef} className="relative bg-white p-6 rounded-lg shadow-lg w-full max-w-md">
            <button
              onClick={() => setShowPopup(false)}
              className="absolute top-2 left-4 font-bold text-gray-500 hover:text-black"
            >
              ✕
            </button>

            <h2 className="text-2xl font-bold mb-4 text-center">Profile</h2>

            <p className="text-black mb-2">Personalize Name:</p>
            <input
              type="text"
              value={namePopupInput}
              onChange={(e) => setNamePopupInput(e.target.value)}
              placeholder="Enter something..."
              className="w-full p-2 border rounded mb-4"
            />

            <p className="text-black mb-2">Enter Allergies - Please separate by comma:</p>
            <input
              type="text"
              value={allergiesPopupInput}
              onChange={(e) => setAllergiesPopupInput(e.target.value)}
              placeholder="Enter something..."
              className="w-full p-2 border rounded mb-4"
            />

            <div className="flex items-center justify-between mb-4">
              <p className="text-black">Location Access:</p>
              <button
                onClick={() => {
                  const newState = !locationEnabled;
                  setLocationEnabled(newState);
                  if (!newState) {
                    setLocation(null);
                    setCity('');
                  } else {
                    getLocation();
                  }
                }}
                className={`px-2 py-1 rounded text-xs ${
                  locationEnabled
                    ? 'bg-red-100 text-red-700 hover:bg-red-200'
                    : 'bg-green-100 text-green-700 hover:bg-green-200'
                }`}
              >
                {locationEnabled ? 'Disable' : 'Enable'}
              </button>
            </div>


            <div className="text-sm text-black ml-1 mb-4">
              {!locationEnabled ? (
                  <p className="text-gray-500 italic">Location disabled</p>
                ) : location ? (
                  <div className="flex items-center space-x-2">
                    <span>📍</span>
                    {city ? (
                      <span>{city}</span>
                    ) : (
                      <span>Lat: {location.latitude.toFixed(2)}, Lon: {location.longitude.toFixed(2)}</span>
                    )}
                  </div>
                ) : locationError ? (
                      <p className="text-red-600 italic">Enable location in browser settings</p>
                    ) : (
                  <p>Loading location...</p>
                )}

            </div>
            <div className="flex justify-end">
              <button
                onClick={() => setShowPopup(false)}
                className="px-4 py-2 bg-purple text-white rounded hover:opacity-90"
              >
                Save
              </button>
            </div>
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
          {loading && !visibleBotResponse && (
            <div className="flex justify-start">
              <p className="px-4 py-2 bg-gray-300 text-black rounded-lg break-words whitespace-pre-wrap max-w-[500px] transition-all duration-300 animate-pulse">
                Thinking...
              </p>
            </div>
          )}

          {visibleBotResponse && (
            <div className="flex justify-start">
              <p className="px-4 py-2 bg-gray-300 text-black rounded-lg break-words whitespace-pre-wrap max-w-[500px] transition-all duration-300">
                {visibleBotResponse}
                <span className="inline-block w-[10px] h-[1em] bg-black ml-1 animate-blink align-middle"></span>
              </p>
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
            className="absolute inset-0 flex flex-col items-center justify-center bg-white/70 z-70 backdrop-blur"
          >
            <img src={pizzaIcon} className="w-[100px] h-[100px] mb-4" />
            <h1 className="text-4xl font-bold mb-4 text-black">Welcome to DeepDish AI!</h1>
            <h2 className="text-2xl font-semibold mb-4 text-black">How can I help you?</h2>
            <form id="init_query_form" onSubmit={handleSubmit} className="w-full max-w-xl px-4">
              <div className="flex gap-2">
                <div className="flex-1 bg-gray-200 rounded-lg p-2 flex">
                  <textarea
                    ref={textareaRef}
                    value={query}
                    onChange={handleQueryChange}
                    onInput={handleTextareaInput}
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
            id="regular_query_form"
            onSubmit={handleSubmit}
            className="fixed bottom-0 w-full flex items-center bg-white justify-center px-4 pb-4 z-50"
          >
            <div className="w-full max-w-3xl flex gap-2">
              <div className="flex-1 outline bg-gray-200 rounded-lg p-2 flex">
                <textarea
                    ref={textareaRefBottom}
                    value={query}
                    onChange={handleQueryChange}
                    onInput={handleTextareaInputBottom}
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