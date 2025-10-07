import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const QuotingTool = () => {
  const [quotes, setQuotes] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState('list'); // 'list', 'create', 'edit', 'view'
  const [selectedQuote, setSelectedQuote] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [analytics, setAnalytics] = useState(null);

  const [newQuote, setNewQuote] = useState({
    title: '',
    customer_name: '',
    customer_email: '',
    customer_phone: '',
    customer_address: {},
    line_items: [],
    tax_settings: {
      tax_rate: 0,
      tax_name: 'Tax',
      is_inclusive: false
    },
    notes: '',
    terms_conditions: '',
    expires_in_days: 30,
    e_signature_required: false,
    created_by: 'current_user'
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [quotesResponse, productsResponse, analyticsResponse] = await Promise.all([
        axios.get(`${API}/quotes`),
        axios.get(`${API}/products-services`),
        axios.get(`${API}/quotes/analytics/summary`)
      ]);
      
      setQuotes(quotesResponse.data);
      setProducts(productsResponse.data);
      setAnalytics(analyticsResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const createQuote = async () => {
    try {
      const response = await axios.post(`${API}/quotes`, newQuote);
      setQuotes([response.data, ...quotes]);
      setNewQuote({
        title: '',
        customer_name: '',
        customer_email: '',
        customer_phone: '',
        customer_address: {},
        line_items: [],
        tax_settings: { tax_rate: 0, tax_name: 'Tax', is_inclusive: false },
        notes: '',
        terms_conditions: '',
        expires_in_days: 30,
        e_signature_required: false,
        created_by: 'current_user'
      });
      setShowCreateModal(false);
      fetchData(); // Refresh analytics
    } catch (error) {
      console.error('Error creating quote:', error);
    }
  };

  const initializeSampleData = async () => {
    try {
      await axios.post(`${API}/quotes/init-sample-data`);
      fetchData(); // Refresh all data after initialization
      alert('Sample data initialized successfully!');
    } catch (error) {
      console.error('Error initializing sample data:', error);
      alert('Error initializing sample data. Please try again.');
    }
  };

  const viewQuote = (quote) => {
    setSelectedQuote(quote);
    setActiveView('view');
  };

  const editQuote = (quote) => {
    setSelectedQuote(quote);
    setActiveView('edit');
  };

  const deleteQuote = async (quoteId) => {
    if (window.confirm('Are you sure you want to delete this quote?')) {
      try {
        await axios.delete(`${API}/quotes/${quoteId}`);
        setQuotes(quotes.filter(q => q.id !== quoteId));
        fetchData(); // Refresh analytics
      } catch (error) {
        console.error('Error deleting quote:', error);
        alert('Error deleting quote. Please try again.');
      }
    }
  };

  const sendQuote = async (quoteId) => {
    try {
      await axios.post(`${API}/quotes/${quoteId}/send`);
      // Update the quote status in local state
      setQuotes(quotes.map(q => 
        q.id === quoteId ? { ...q, status: 'sent' } : q
      ));
      fetchData(); // Refresh analytics
      alert('Quote sent successfully!');
    } catch (error) {
      console.error('Error sending quote:', error);
      alert('Error sending quote. Please try again.');
    }
  };

  const sendQuote = async (quoteId) => {
    try {
      await axios.post(`${API}/quotes/${quoteId}/send`);
      setQuotes(quotes.map(quote => 
        quote.id === quoteId ? { ...quote, status: 'sent', sent_at: new Date().toISOString() } : quote
      ));
    } catch (error) {
      console.error('Error sending quote:', error);
    }
  };

  const addLineItem = () => {
    setNewQuote({
      ...newQuote,
      line_items: [...newQuote.line_items, {
        product_service_id: '',
        quantity: 1,
        discount_percentage: 0,
        discount_amount: 0,
        pricing_tier: 'standard'
      }]
    });
  };

  const updateLineItem = (index, field, value) => {
    const updatedItems = [...newQuote.line_items];
    updatedItems[index][field] = value;
    setNewQuote({ ...newQuote, line_items: updatedItems });
  };

  const removeLineItem = (index) => {
    const updatedItems = newQuote.line_items.filter((_, i) => i !== index);
    setNewQuote({ ...newQuote, line_items: updatedItems });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
      case 'sent': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200';
      case 'viewed': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200';
      case 'accepted': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200';
      case 'rejected': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200';
      case 'expired': return 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const initializeSampleData = async () => {
    try {
      await axios.post(`${API}/quotes/initialize-sample-data`);
      fetchData();
    } catch (error) {
      console.error('Error initializing sample data:', error);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Quoting Tool</h1>
          <p className="text-gray-600 dark:text-gray-400">AI-powered quote generation and management</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={initializeSampleData}
            className="btn-secondary"
          >
            Initialize Sample Data
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create Quote
          </button>
        </div>
      </div>

      {/* Analytics Dashboard */}
      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Quotes</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.total_quotes}</p>
              </div>
              <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
                <span className="text-blue-600 dark:text-blue-400">📄</span>
              </div>
            </div>
          </div>
          
          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Conversion Rate</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.conversion_rate}%</p>
              </div>
              <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                <span className="text-green-600 dark:text-green-400">📈</span>
              </div>
            </div>
          </div>

          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Value</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{formatCurrency(analytics.total_value)}</p>
              </div>
              <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
                <span className="text-purple-600 dark:text-purple-400">💰</span>
              </div>
            </div>
          </div>

          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Quote Value</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">{formatCurrency(analytics.average_quote_value)}</p>
              </div>
              <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
                <span className="text-orange-600 dark:text-orange-400">📊</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Quotes List */}
      <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200/50 dark:border-gray-700/50">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">All Quotes</h2>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700/50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Quote</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Customer</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Created</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {quotes.map((quote) => (
                <tr key={quote.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">{quote.quote_number}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">{quote.title}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-white">{quote.customer_name}</div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">{quote.customer_email}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                    {formatCurrency(quote.total_amount)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`tag ${getStatusColor(quote.status)}`}>
                      {quote.status.charAt(0).toUpperCase() + quote.status.slice(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {new Date(quote.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button 
                      onClick={() => viewQuote(quote)}
                      className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
                    >
                      View
                    </button>
                    {quote.status === 'draft' && (
                      <button
                        onClick={() => sendQuote(quote.id)}
                        className="text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300"
                      >
                        Send
                      </button>
                    )}
                    <button 
                      onClick={() => editQuote(quote)}
                      className="text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                    >
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {quotes.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📄</div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No quotes found</h3>
          <p className="text-gray-600 dark:text-gray-400">Create your first quote to get started</p>
        </div>
      )}

      {/* Create Quote Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Create New Quote</h3>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Customer Information */}
              <div className="space-y-4">
                <h4 className="text-md font-medium text-gray-900 dark:text-white">Customer Information</h4>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Quote Title</label>
                  <input
                    type="text"
                    value={newQuote.title}
                    onChange={(e) => setNewQuote({ ...newQuote, title: e.target.value })}
                    className="form-input"
                    placeholder="Enter quote title"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Customer Name</label>
                  <input
                    type="text"
                    value={newQuote.customer_name}
                    onChange={(e) => setNewQuote({ ...newQuote, customer_name: e.target.value })}
                    className="form-input"
                    placeholder="Enter customer name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                  <input
                    type="email"
                    value={newQuote.customer_email}
                    onChange={(e) => setNewQuote({ ...newQuote, customer_email: e.target.value })}
                    className="form-input"
                    placeholder="Enter email address"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Phone</label>
                  <input
                    type="tel"
                    value={newQuote.customer_phone}
                    onChange={(e) => setNewQuote({ ...newQuote, customer_phone: e.target.value })}
                    className="form-input"
                    placeholder="Enter phone number"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tax Rate (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newQuote.tax_settings.tax_rate}
                    onChange={(e) => setNewQuote({
                      ...newQuote,
                      tax_settings: { ...newQuote.tax_settings, tax_rate: parseFloat(e.target.value) || 0 }
                    })}
                    className="form-input"
                    placeholder="Enter tax rate"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Expires in (days)</label>
                  <input
                    type="number"
                    value={newQuote.expires_in_days}
                    onChange={(e) => setNewQuote({ ...newQuote, expires_in_days: parseInt(e.target.value) || 30 })}
                    className="form-input"
                    placeholder="30"
                  />
                </div>
              </div>

              {/* Line Items */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-md font-medium text-gray-900 dark:text-white">Line Items</h4>
                  <button
                    onClick={addLineItem}
                    className="text-sm bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-lg transition-colors"
                  >
                    Add Item
                  </button>
                </div>
                
                <div className="space-y-3 max-h-60 overflow-y-auto">
                  {newQuote.line_items.map((item, index) => (
                    <div key={index} className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Item {index + 1}</span>
                        <button
                          onClick={() => removeLineItem(index)}
                          className="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <select
                          value={item.product_service_id}
                          onChange={(e) => updateLineItem(index, 'product_service_id', e.target.value)}
                          className="form-input text-sm"
                        >
                          <option value="">Select Product/Service</option>
                          {products.map(product => (
                            <option key={product.id} value={product.id}>
                              {product.name} - {formatCurrency(product.unit_price)}
                            </option>
                          ))}
                        </select>
                        <input
                          type="number"
                          step="0.01"
                          value={item.quantity}
                          onChange={(e) => updateLineItem(index, 'quantity', parseFloat(e.target.value) || 1)}
                          className="form-input text-sm"
                          placeholder="Quantity"
                        />
                        <select
                          value={item.pricing_tier}
                          onChange={(e) => updateLineItem(index, 'pricing_tier', e.target.value)}
                          className="form-input text-sm"
                        >
                          <option value="standard">Standard</option>
                          <option value="premium">Premium</option>
                          <option value="enterprise">Enterprise</option>
                        </select>
                        <input
                          type="number"
                          step="0.01"
                          value={item.discount_percentage}
                          onChange={(e) => updateLineItem(index, 'discount_percentage', parseFloat(e.target.value) || 0)}
                          className="form-input text-sm"
                          placeholder="Discount %"
                        />
                      </div>
                    </div>
                  ))}
                  
                  {newQuote.line_items.length === 0 && (
                    <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                      <p className="text-sm">No line items added yet. Click "Add Item" to get started.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Notes and Terms */}
            <div className="mt-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Notes</label>
                <textarea
                  value={newQuote.notes}
                  onChange={(e) => setNewQuote({ ...newQuote, notes: e.target.value })}
                  className="form-input"
                  rows="3"
                  placeholder="Add any notes for this quote"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Terms & Conditions</label>
                <textarea
                  value={newQuote.terms_conditions}
                  onChange={(e) => setNewQuote({ ...newQuote, terms_conditions: e.target.value })}
                  className="form-input"
                  rows="3"
                  placeholder="Enter terms and conditions"
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={newQuote.e_signature_required}
                  onChange={(e) => setNewQuote({ ...newQuote, e_signature_required: e.target.checked })}
                  className="custom-checkbox mr-2"
                />
                <label className="text-sm text-gray-700 dark:text-gray-300">Require e-signature</label>
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={createQuote}
                className="flex-1 btn-primary"
                disabled={!newQuote.title || !newQuote.customer_name || !newQuote.customer_email || newQuote.line_items.length === 0}
              >
                Create Quote
              </button>
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuotingTool;