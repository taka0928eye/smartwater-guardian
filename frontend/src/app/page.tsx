'use client';

import { useEffect, useState } from 'react';
import axios from 'axios';

export default function Home() {
  const [status, setStatus] = useState<string>('Connecting...');

  useEffect(() => {
    axios.get('http://localhost:8000/')
      .then(res => setStatus(res.data.message))
      .catch(() => setStatus('Backend connection failed'));
  }, []);

  return (
    <main className="p-8 font-sans">
      <h1 className="text-2xl font-bold mb-4">SmartWater Guardian Dashboard</h1>
      <p className="text-lg">
        Backend Status: <span className="font-semibold text-blue-600">{status}</span>
      </p>
    </main>
  );
}