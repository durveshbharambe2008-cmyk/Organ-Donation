// API fetch wrapper with centralized error and auth handling
const api = {
  async request(method, url, body = null) {
    const options = {
      method: method.toUpperCase(),
      headers: {
        'Accept': 'application/json'
      }
    };

    if (body !== null) {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }

    let response;
    try {
      response = await fetch(url, options);
    } catch (err) {
      throw new Error('Network error: Unable to reach the server.');
    }

    if (response.status === 401) {
      // Exclude /api/auth/login from redirecting
      if (!url.includes('/api/auth/login')) {
        window.location.href = '/login.html';
      }
      const data = await response.json().catch(() => ({}));
      throw new Error(data.error || 'Please sign in.');
    }

    const contentType = response.headers.get('content-type') || '';
    let data = {};
    if (contentType.includes('application/json')) {
      data = await response.json().catch(() => ({}));
    }

    if (!response.ok) {
      const errorMsg = data.error || `Request failed with status ${response.status}`;
      throw new Error(errorMsg);
    }

    return data;
  },

  get(url) {
    return this.request('GET', url);
  },

  post(url, body) {
    return this.request('POST', url, body);
  },

  put(url, body) {
    return this.request('PUT', url, body);
  },

  delete(url) {
    return this.request('DELETE', url);
  }
};
