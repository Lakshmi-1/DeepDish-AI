import { useState, useEffect } from 'react';

function App() {
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleQueryChange = (e) => {
    setQuery(e.target.value);
  };

  const fetchQueryResult = async () => {
    if (!query) return;

    setLoading(true);
    setResults([]); // Clear previous results
    try {
      const response = await fetch('http://127.0.0.1:5000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query }),
      });

      const data = await response.json();
      if (data.result) {
        setResults(data.result.result);

        setMessage(`Found ${data.result.length} result(s)`);
      } else {
        setMessage('No results found.');
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      setMessage('An error occurred while fetching data.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchQueryResult();
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gradient-to-r from-mint-500 via-pink-500 to-red-500">
      <div className="text-center">
        <img src="/pizza.png" alt="logo" className="w-32 h-32 mx-auto" />
        <h1 className="text-6xl font-extrabold text-white drop-shadow-lg">
          {loading ? 'Loading...' : message}
        </h1>
        <p className="mt-4 text-2xl text-white italic">
          Welcome to our application!
        </p>
        <form onSubmit={handleSubmit} className="mt-6">
          <input
            type="text"
            value={query}
            onChange={handleQueryChange}
            className="p-2 rounded"
            placeholder="Enter your query"
          />
          <button type="submit" className="ml-4 p-2 bg-blue-500 text-white rounded">
            Submit
          </button>
        </form>
        {results}
      </div>
    </div>
  );
}

export default App;