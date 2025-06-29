import React, { useState, useEffect } from 'react';
import './App.css';

const API_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);

  // Auth forms
  const [isLogin, setIsLogin] = useState(true);
  const [authForm, setAuthForm] = useState({
    email: '',
    password: '',
    full_name: '',
    country: '',
    phone: ''
  });

  // Data states
  const [dashboard, setDashboard] = useState(null);
  const [deposits, setDeposits] = useState([]);
  const [applications, setApplications] = useState([]);
  const [repayments, setRepayments] = useState([]);

  // Form states
  const [depositForm, setDepositForm] = useState({ amount: '', description: '' });
  const [applicationForm, setApplicationForm] = useState({
    amount: '',
    purpose: '',
    requested_duration_months: '',
    description: ''
  });

  useEffect(() => {
    if (token) {
      fetchUserProfile();
    }
  }, [token]);

  const api = async (endpoint, options = {}) => {
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` })
      },
      ...options
    };

    if (options.body) {
      config.body = JSON.stringify(options.body);
    }

    const response = await fetch(`${API_URL}${endpoint}`, config);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Network error' }));
      throw new Error(error.detail || 'Something went wrong');
    }
    
    return response.json();
  };

  const fetchUserProfile = async () => {
    try {
      const userData = await api('/api/auth/me');
      setUser(userData);
      fetchDashboard();
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      logout();
    }
  };

  const fetchDashboard = async () => {
    try {
      const dashboardData = await api('/api/dashboard');
      setDashboard(dashboardData);
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
    }
  };

  const fetchDeposits = async () => {
    try {
      const depositsData = await api('/api/deposits');
      setDeposits(depositsData);
    } catch (error) {
      console.error('Failed to fetch deposits:', error);
    }
  };

  const fetchApplications = async () => {
    try {
      const applicationsData = await api('/api/finance-applications');
      setApplications(applicationsData);
    } catch (error) {
      console.error('Failed to fetch applications:', error);
    }
  };

  const fetchRepayments = async () => {
    try {
      const repaymentsData = await api('/api/repayments');
      setRepayments(repaymentsData);
    } catch (error) {
      console.error('Failed to fetch repayments:', error);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
      const body = isLogin 
        ? { email: authForm.email, password: authForm.password }
        : authForm;

      const data = await api(endpoint, { method: 'POST', body });
      
      setToken(data.access_token);
      localStorage.setItem('token', data.access_token);
      setUser(data.user);
      fetchDashboard();
      
      setAuthForm({ email: '', password: '', full_name: '', country: '', phone: '' });
    } catch (error) {
      alert(error.message);
    }
    setLoading(false);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    setActiveTab('dashboard');
  };

  const handleDeposit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api('/api/deposits', { 
        method: 'POST', 
        body: { 
          amount: parseFloat(depositForm.amount),
          description: depositForm.description 
        }
      });
      
      setDepositForm({ amount: '', description: '' });
      fetchDashboard();
      fetchDeposits();
      alert('Deposit recorded successfully!');
    } catch (error) {
      alert(error.message);
    }
    setLoading(false);
  };

  const handleApplication = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await api('/api/finance-applications', {
        method: 'POST',
        body: {
          amount: parseFloat(applicationForm.amount),
          purpose: applicationForm.purpose,
          requested_duration_months: parseInt(applicationForm.requested_duration_months),
          description: applicationForm.description
        }
      });

      setApplicationForm({ amount: '', purpose: '', requested_duration_months: '', description: '' });
      fetchDashboard();
      fetchApplications();
      alert('Finance application submitted successfully!');
    } catch (error) {
      alert(error.message);
    }
    setLoading(false);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusBadge = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      under_review: 'bg-blue-100 text-blue-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      disbursed: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      paid: 'bg-green-100 text-green-800',
      overdue: 'bg-red-100 text-red-800'
    };

    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Fund Manager</h1>
            <p className="text-gray-600">Your personal finance companion</p>
          </div>

          <div className="flex bg-gray-100 rounded-lg p-1 mb-6">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                isLogin ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'
              }`}
            >
              Login
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                !isLogin ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleAuth} className="space-y-4">
            <div>
              <input
                type="email"
                placeholder="Email"
                value={authForm.email}
                onChange={(e) => setAuthForm({...authForm, email: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            <div>
              <input
                type="password"
                placeholder="Password"
                value={authForm.password}
                onChange={(e) => setAuthForm({...authForm, password: e.target.value})}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>
            
            {!isLogin && (
              <>
                <div>
                  <input
                    type="text"
                    placeholder="Full Name"
                    value={authForm.full_name}
                    onChange={(e) => setAuthForm({...authForm, full_name: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <input
                    type="text"
                    placeholder="Country"
                    value={authForm.country}
                    onChange={(e) => setAuthForm({...authForm, country: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <div>
                  <input
                    type="tel"
                    placeholder="Phone (optional)"
                    value={authForm.phone}
                    onChange={(e) => setAuthForm({...authForm, phone: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors disabled:opacity-50"
            >
              {loading ? 'Processing...' : (isLogin ? 'Login' : 'Create Account')}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Fund Manager</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">Welcome, {user.full_name}</span>
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                {user.role.replace('_', ' ').toUpperCase()}
              </span>
              <button
                onClick={logout}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation */}
        <nav className="flex space-x-8 mb-8">
          {['dashboard', 'deposits', 'applications', 'repayments'].map((tab) => (
            <button
              key={tab}
              onClick={() => {
                setActiveTab(tab);
                if (tab === 'deposits') fetchDeposits();
                if (tab === 'applications') fetchApplications();
                if (tab === 'repayments') fetchRepayments();
              }}
              className={`px-3 py-2 rounded-md text-sm font-medium ${
                activeTab === tab
                  ? 'bg-blue-100 text-blue-700'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>

        {/* Content */}
        {activeTab === 'dashboard' && dashboard && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-md">
                    <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Deposits</p>
                    <p className="text-2xl font-semibold text-gray-900">{formatCurrency(dashboard.total_deposits)}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-md">
                    <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Finance Applications</p>
                    <p className="text-2xl font-semibold text-gray-900">{dashboard.total_applications}</p>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <div className="p-2 bg-red-100 rounded-md">
                    <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Pending Repayments</p>
                    <p className="text-2xl font-semibold text-gray-900">{formatCurrency(dashboard.pending_repayments)}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b">
                  <h3 className="text-lg font-medium text-gray-900">Recent Deposits</h3>
                </div>
                <div className="p-6">
                  {dashboard.recent_deposits.length > 0 ? (
                    <div className="space-y-3">
                      {dashboard.recent_deposits.map((deposit) => (
                        <div key={deposit.id} className="flex justify-between items-center">
                          <div>
                            <p className="text-sm font-medium text-gray-900">{formatCurrency(deposit.amount)}</p>
                            <p className="text-xs text-gray-500">{formatDate(deposit.created_at)}</p>
                          </div>
                          {getStatusBadge(deposit.status)}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500">No deposits yet</p>
                  )}
                </div>
              </div>

              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b">
                  <h3 className="text-lg font-medium text-gray-900">Recent Applications</h3>
                </div>
                <div className="p-6">
                  {dashboard.recent_applications.length > 0 ? (
                    <div className="space-y-3">
                      {dashboard.recent_applications.map((app) => (
                        <div key={app.id} className="flex justify-between items-center">
                          <div>
                            <p className="text-sm font-medium text-gray-900">{formatCurrency(app.amount)}</p>
                            <p className="text-xs text-gray-500">{app.purpose}</p>
                          </div>
                          {getStatusBadge(app.status)}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500">No applications yet</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'deposits' && (
          <div className="space-y-6">
            {/* Add Deposit Form */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Record New Deposit</h3>
              <form onSubmit={handleDeposit} className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <input
                  type="number"
                  step="0.01"
                  placeholder="Amount"
                  value={depositForm.amount}
                  onChange={(e) => setDepositForm({...depositForm, amount: e.target.value})}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
                <input
                  type="text"
                  placeholder="Description (optional)"
                  value={depositForm.description}
                  onChange={(e) => setDepositForm({...depositForm, description: e.target.value})}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Adding...' : 'Add Deposit'}
                </button>
              </form>
            </div>

            {/* Deposits List */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <h3 className="text-lg font-medium text-gray-900">Your Deposits</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {deposits.map((deposit) => (
                      <tr key={deposit.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {formatCurrency(deposit.amount)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {deposit.description || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(deposit.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(deposit.status)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {deposits.length === 0 && (
                  <div className="p-6 text-center text-gray-500">
                    No deposits found. Record your first deposit above!
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'applications' && (
          <div className="space-y-6">
            {/* Add Application Form */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Submit Finance Application</h3>
              <form onSubmit={handleApplication} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <input
                    type="number"
                    step="0.01"
                    placeholder="Requested Amount"
                    value={applicationForm.amount}
                    onChange={(e) => setApplicationForm({...applicationForm, amount: e.target.value})}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                  <input
                    type="number"
                    placeholder="Duration (months)"
                    value={applicationForm.requested_duration_months}
                    onChange={(e) => setApplicationForm({...applicationForm, requested_duration_months: e.target.value})}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    required
                  />
                </div>
                <input
                  type="text"
                  placeholder="Purpose"
                  value={applicationForm.purpose}
                  onChange={(e) => setApplicationForm({...applicationForm, purpose: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
                <textarea
                  placeholder="Additional Description (optional)"
                  value={applicationForm.description}
                  onChange={(e) => setApplicationForm({...applicationForm, description: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows="3"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Submitting...' : 'Submit Application'}
                </button>
              </form>
            </div>

            {/* Applications List */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <h3 className="text-lg font-medium text-gray-900">Your Applications</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Purpose</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {applications.map((app) => (
                      <tr key={app.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {formatCurrency(app.amount)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {app.purpose}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {app.requested_duration_months} months
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(app.created_at)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(app.status)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {applications.length === 0 && (
                  <div className="p-6 text-center text-gray-500">
                    No applications found. Submit your first application above!
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'repayments' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b">
              <h3 className="text-lg font-medium text-gray-900">Your Repayments</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Installment</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Due Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Paid Date</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {repayments.map((repayment) => (
                    <tr key={repayment.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {formatCurrency(repayment.amount)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        #{repayment.installment_number}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(repayment.due_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {repayment.paid_date ? formatDate(repayment.paid_date) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(repayment.status)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {repayments.length === 0 && (
                <div className="p-6 text-center text-gray-500">
                  No repayments found.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;