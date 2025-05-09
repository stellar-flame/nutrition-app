const fetch = require('node-fetch');

async function testApiKey() {
  try {
    const response = await fetch('http://localhost:3001/openai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: [{ role: 'user', content: "Hello" }],
        model: 'gpt-4',
        temperature: 0,
        max_tokens: 150,
      }),
    });

    const data = await response.json();
    console.log('Backend server response:', JSON.stringify(data, null, 2));
  } catch (error) {
    console.error('Error testing backend server:', error);
  }
}

testApiKey();
