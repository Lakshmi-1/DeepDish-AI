import { useState, useEffect } from 'react'


function App() {
  const [count, setCount] = useState(0)
  const [message, setMessage] = useState('')

  const fetchAPT = async () => {
    const response = await fetch('http://127.0.0.1:8080/api/test')
    const data = await response.json()
    setMessage(data.message)
  }

  useEffect(() => {
    fetchAPT()
  },[])

  return (
    <div className="flex justify-center items-center min-h-screen bg-gradient-to-r from-mint-500 via-pink-500 to-red-500">
      <div className="text-center">
        <img src="/pizza.png" alt="logo" className="w-32 h-32 mx-auto" />
        <h1 className="text-6xl font-extrabold text-white drop-shadow-lg">
          {message}
        </h1>
        <p className="mt-4 text-2xl text-white italic">
          Welcome to our application!
        </p>
      </div>
    </div>
  )
}

export default App
