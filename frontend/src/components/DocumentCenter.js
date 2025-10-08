import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DocumentCenter = () => {
  const [activeView, setActiveView] = useState('templates'); // 'templates', 'documents', 'categories'
  const [templates, setTemplates] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [showConversionModal, setShowConversionModal] = useState(false);

  const [newDocument, setNewDocument] = useState({
    title: '',
    description: '',
    template_id: '',
    type: 'custom',
    category_id: '',
    content: '',
    file_format: 'pdf',
    access_level: 'private',
    signature_required: false,
    signers: [],
    created_by: 'current_user',
    tags: []
  });

  const [newTemplate, setNewTemplate] = useState({
    title: '',
    description: '',
    type: 'custom',
    category_id: '',
    content: '',
    variables: [],
    file_format: 'pdf',
    access_level: 'team',
    created_by: 'current_user',
    tags: []
  });

  const [conversionRequest, setConversionRequest] = useState({
    file_content: '',
    source_format: 'docx',
    target_format: 'pdf',
    document_title: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [templatesResponse, documentsResponse, categoriesResponse] = await Promise.all([
        axios.get(`${API}/document-templates`),
        axios.get(`${API}/documents`),
        axios.get(`${API}/document-categories`)
      ]);
      
      setTemplates(templatesResponse.data);
      setDocuments(documentsResponse.data);
      setCategories(categoriesResponse.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const initializeSampleData = async () => {
    try {
      await axios.post(`${API}/documents/initialize-sample-data`);
      fetchData();
    } catch (error) {
      console.error('Error initializing sample data:', error);
    }
  };

  const createDocument = async () => {
    try {
      const response = await axios.post(`${API}/documents`, newDocument);
      setDocuments([response.data, ...documents]);
      setNewDocument({
        title: '',
        description: '',
        template_id: '',
        type: 'custom',
        category_id: '',
        content: '',
        file_format: 'pdf',
        access_level: 'private',
        signature_required: false,
        signers: [],
        created_by: 'current_user',
        tags: []
      });
      setShowCreateModal(false);
      setActiveView('documents');
    } catch (error) {
      console.error('Error creating document:', error);
    }
  };

  const createTemplate = async () => {
    try {
      const response = await axios.post(`${API}/document-templates`, newTemplate);
      setTemplates([response.data, ...templates]);
      setNewTemplate({
        title: '',
        description: '',
        type: 'custom',
        category_id: '',
        content: '',
        variables: [],
        file_format: 'pdf',
        access_level: 'team',
        created_by: 'current_user',
        tags: []
      });
      setShowTemplateModal(false);
    } catch (error) {
      console.error('Error creating template:', error);
    }
  };

  const convertFile = async () => {
    try {
      const response = await axios.post(`${API}/documents/convert`, conversionRequest);
      
      // Create a download link for the converted file
      const blob = new Blob([Uint8Array.from(atob(response.data.converted_content), c => c.charCodeAt(0))], {
        type: `application/${response.data.target_format}`
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `converted_${conversionRequest.document_title || 'document'}.${response.data.target_format}`;
      a.click();
      window.URL.revokeObjectURL(url);
      
      setShowConversionModal(false);
      setConversionRequest({
        file_content: '',
        source_format: 'docx',
        target_format: 'pdf',
        document_title: ''
      });
    } catch (error) {
      console.error('Error converting file:', error);
    }
  };

  const sendForSignature = async (documentId) => {
    try {
      const signers = [
        { name: 'John Smith', email: 'john@example.com', role: 'signer' }
      ];
      
      await axios.post(`${API}/documents/${documentId}/send-for-signature`, {
        document_id: documentId,
        signers: signers,
        email_subject: 'Please sign this document',
        email_message: 'Please review and sign the attached document.',
        send_reminders: true
      });
      
      // Update document status locally
      setDocuments(documents.map(doc => 
        doc.id === documentId 
          ? { ...doc, status: 'pending_signature', docusign_status: 'sent' }
          : doc
      ));
    } catch (error) {
      console.error('Error sending for signature:', error);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64 = e.target.result.split(',')[1];
        setConversionRequest({
          ...conversionRequest,
          file_content: base64,
          document_title: file.name.split('.')[0]
        });
      };
      reader.readAsDataURL(file);
    }
  };

  // New navigation and interaction functions
  const useTemplate = (template) => {
    setSelectedTemplate(template);
    setNewDocument({
      ...newDocument,
      template_id: template.id,
      title: `New ${template.name}`,
      content: template.content,
      type: template.type,
      category_id: template.category_id
    });
    setShowCreateModal(true);
  };

  const previewTemplate = (template) => {
    setSelectedTemplate(template);
    setShowTemplateModal(true);
  };

  const viewDocument = (document) => {
    alert(`Viewing document: ${document.title}\nStatus: ${document.status}\nCreated: ${new Date(document.created_at).toLocaleDateString()}`);
  };

  const editDocument = (document) => {
    setSelectedTemplate(document);
    setNewDocument({
      title: document.title,
      description: document.description,
      template_id: document.template_id || '',
      type: document.type,
      category_id: document.category_id,
      content: document.content,
      file_format: document.file_format,
      access_level: document.access_level,
      signature_required: document.signature_required,
      signers: document.signers || [],
      created_by: document.created_by
    });
    setShowCreateModal(true);
  };

  const viewCategoryDocuments = (categoryId) => {
    setSelectedCategory(categoryId);
    setActiveView('documents');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
      case 'active': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200';
      case 'pending_signature': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200';
      case 'signed': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200';
      case 'expired': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
    }
  };

  const getCategoryById = (categoryId) => {
    return categories.find(cat => cat.id === categoryId);
  };

  const filteredTemplates = selectedCategory === 'all' 
    ? templates 
    : templates.filter(template => template.category_id === selectedCategory);

  const filteredDocuments = selectedCategory === 'all' 
    ? documents 
    : documents.filter(document => document.category_id === selectedCategory);

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
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Document Center</h1>
          <p className="text-gray-600 dark:text-gray-400">Templates, forms, file conversion, and DocuSign integration</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={initializeSampleData}
            className="btn-secondary"
          >
            Initialize Sample Data
          </button>
          <button
            onClick={() => setShowConversionModal(true)}
            className="bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition-all duration-200"
          >
            <svg className="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
            </svg>
            Convert Files
          </button>
          <button
            onClick={() => setShowTemplateModal(true)}
            className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-all duration-200"
          >
            <svg className="w-5 h-5 mr-2 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create Template
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            Create Document
          </button>
        </div>
      </div>

      {/* View Tabs */}
      <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-4 border border-gray-200/50 dark:border-gray-700/50 mb-6">
        <div className="flex space-x-2">
          {[
            { key: 'templates', label: 'Templates', icon: '📄', count: templates.length },
            { key: 'documents', label: 'Documents', icon: '📋', count: documents.length },
            { key: 'categories', label: 'Categories', icon: '📁', count: categories.length }
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveView(tab.key)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                activeView === tab.key
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label} ({tab.count})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Category Filter */}
      {(activeView === 'templates' || activeView === 'documents') && (
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-4 border border-gray-200/50 dark:border-gray-700/50 mb-6">
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedCategory('all')}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-all duration-200 ${
                selectedCategory === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              All Categories
            </button>
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-all duration-200 ${
                  selectedCategory === category.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
                style={{
                  backgroundColor: selectedCategory === category.id ? category.color : undefined
                }}
              >
                <span className="mr-1">{category.icon}</span>
                {category.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Templates View */}
      {activeView === 'templates' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredTemplates.map((template) => {
            const category = getCategoryById(template.category_id);
            return (
              <div key={template.id} className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50 card-hover">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
                      {template.title}
                    </h3>
                    {category && (
                      <span 
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white mb-2"
                        style={{ backgroundColor: category.color }}
                      >
                        <span className="mr-1">{category.icon}</span>
                        {category.name}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400">
                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    <span>{template.usage_count}</span>
                  </div>
                </div>
                
                {template.description && (
                  <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-3">
                    {template.description}
                  </p>
                )}
                
                <div className="flex items-center justify-between mb-4">
                  <span className={`tag tag-blue`}>
                    {template.type.replace('_', ' ')}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400 uppercase">
                    {template.file_format}
                  </span>
                </div>
                
                {template.tags && template.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-4">
                    {template.tags.slice(0, 3).map((tag, index) => (
                      <span key={index} className="tag tag-gray text-xs">
                        {tag}
                      </span>
                    ))}
                    {template.tags.length > 3 && (
                      <span className="text-xs text-gray-500 dark:text-gray-400">+{template.tags.length - 3}</span>
                    )}
                  </div>
                )}
                
                <div className="flex space-x-2">
                  <button
                    onClick={() => {
                      setNewDocument({ ...newDocument, template_id: template.id, title: `New ${template.title}` });
                      setShowCreateModal(true);
                    }}
                    className="flex-1 text-sm bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-medium py-2 px-3 rounded-lg transition-all duration-200"
                  >
                    Use Template
                  </button>
                  <button className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 font-medium py-2 px-3 rounded-lg border border-gray-300 dark:border-gray-600 transition-colors">
                    Preview
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Documents View */}
      {activeView === 'documents' && (
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl border border-gray-200/50 dark:border-gray-700/50 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200/50 dark:border-gray-700/50">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">All Documents</h2>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700/50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Document</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredDocuments.map((document) => {
                  const category = getCategoryById(document.category_id);
                  return (
                    <tr key={document.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                            <span className="text-white font-medium text-sm">
                              {document.file_format.toUpperCase()}
                            </span>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900 dark:text-white">{document.title}</div>
                            {document.description && (
                              <div className="text-sm text-gray-500 dark:text-gray-400 truncate max-w-xs">
                                {document.description}
                              </div>
                            )}
                            {category && (
                              <span 
                                className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white mt-1"
                                style={{ backgroundColor: category.color }}
                              >
                                <span className="mr-1">{category.icon}</span>
                                {category.name}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="tag tag-blue">
                          {document.type.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`tag ${getStatusColor(document.status)}`}>
                          {document.status.replace('_', ' ')}
                        </span>
                        {document.docusign_status && (
                          <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            DocuSign: {document.docusign_status}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {new Date(document.created_at).toLocaleDateString()}
                        <div className="text-xs">v{document.version}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                        <button className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300">
                          View
                        </button>
                        <button className="text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300">
                          Edit
                        </button>
                        {document.signature_required && document.status === 'active' && (
                          <button
                            onClick={() => sendForSignature(document.id)}
                            className="text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300"
                          >
                            Send for Signature
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Categories View */}
      {activeView === 'categories' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {categories.map((category) => (
            <div key={category.id} className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50 card-hover">
              <div className="flex items-center space-x-4 mb-4">
                <div 
                  className="w-12 h-12 rounded-lg flex items-center justify-center text-white text-xl"
                  style={{ backgroundColor: category.color }}
                >
                  {category.icon}
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{category.name}</h3>
                  {category.description && (
                    <p className="text-gray-600 dark:text-gray-400 text-sm">{category.description}</p>
                  )}
                </div>
              </div>
              
              <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
                <span>
                  {templates.filter(t => t.category_id === category.id).length} templates,{' '}
                  {documents.filter(d => d.category_id === category.id).length} documents
                </span>
                <button className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium">
                  View All
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Empty States */}
      {((activeView === 'templates' && filteredTemplates.length === 0) ||
        (activeView === 'documents' && filteredDocuments.length === 0) ||
        (activeView === 'categories' && categories.length === 0)) && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">
            {activeView === 'templates' ? '📄' : activeView === 'documents' ? '📋' : '📁'}
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No {activeView} found
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            {activeView === 'templates' ? 'Create your first template to get started' :
             activeView === 'documents' ? 'Create your first document to get started' :
             'Categories will help organize your documents and templates'}
          </p>
        </div>
      )}

      {/* Create Document Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Create New Document</h3>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Title</label>
                  <input
                    type="text"
                    value={newDocument.title}
                    onChange={(e) => setNewDocument({ ...newDocument, title: e.target.value })}
                    className="form-input"
                    placeholder="Document title"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
                  <select
                    value={newDocument.type}
                    onChange={(e) => setNewDocument({ ...newDocument, type: e.target.value })}
                    className="form-input"
                  >
                    <option value="contract">Contract</option>
                    <option value="form">Form</option>
                    <option value="template">Template</option>
                    <option value="invoice">Invoice</option>
                    <option value="proposal">Proposal</option>
                    <option value="agreement">Agreement</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                <textarea
                  value={newDocument.description}
                  onChange={(e) => setNewDocument({ ...newDocument, description: e.target.value })}
                  className="form-input"
                  rows="3"
                  placeholder="Document description"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Category</label>
                  <select
                    value={newDocument.category_id}
                    onChange={(e) => setNewDocument({ ...newDocument, category_id: e.target.value })}
                    className="form-input"
                  >
                    <option value="">Select category</option>
                    {categories.map(category => (
                      <option key={category.id} value={category.id}>{category.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Template</label>
                  <select
                    value={newDocument.template_id}
                    onChange={(e) => setNewDocument({ ...newDocument, template_id: e.target.value })}
                    className="form-input"
                  >
                    <option value="">Select template (optional)</option>
                    {templates.map(template => (
                      <option key={template.id} value={template.id}>{template.title}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Content</label>
                <textarea
                  value={newDocument.content}
                  onChange={(e) => setNewDocument({ ...newDocument, content: e.target.value })}
                  className="form-input"
                  rows="8"
                  placeholder="Document content (HTML supported)"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">File Format</label>
                  <select
                    value={newDocument.file_format}
                    onChange={(e) => setNewDocument({ ...newDocument, file_format: e.target.value })}
                    className="form-input"
                  >
                    <option value="pdf">PDF</option>
                    <option value="docx">DOCX</option>
                    <option value="html">HTML</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Access Level</label>
                  <select
                    value={newDocument.access_level}
                    onChange={(e) => setNewDocument({ ...newDocument, access_level: e.target.value })}
                    className="form-input"
                  >
                    <option value="private">Private</option>
                    <option value="team">Team</option>
                    <option value="organization">Organization</option>
                  </select>
                </div>
                <div className="flex items-center mt-6">
                  <input
                    type="checkbox"
                    checked={newDocument.signature_required}
                    onChange={(e) => setNewDocument({ ...newDocument, signature_required: e.target.checked })}
                    className="custom-checkbox mr-2"
                  />
                  <label className="text-sm text-gray-700 dark:text-gray-300">Require signature</label>
                </div>
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={createDocument}
                className="flex-1 btn-primary"
                disabled={!newDocument.title || !newDocument.content}
              >
                Create Document
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

      {/* Create Template Modal */}
      {showTemplateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Create New Template</h3>
            
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Title</label>
                  <input
                    type="text"
                    value={newTemplate.title}
                    onChange={(e) => setNewTemplate({ ...newTemplate, title: e.target.value })}
                    className="form-input"
                    placeholder="Template title"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
                  <select
                    value={newTemplate.type}
                    onChange={(e) => setNewTemplate({ ...newTemplate, type: e.target.value })}
                    className="form-input"
                  >
                    <option value="contract">Contract</option>
                    <option value="form">Form</option>
                    <option value="template">Template</option>
                    <option value="invoice">Invoice</option>
                    <option value="proposal">Proposal</option>
                    <option value="agreement">Agreement</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                <textarea
                  value={newTemplate.description}
                  onChange={(e) => setNewTemplate({ ...newTemplate, description: e.target.value })}
                  className="form-input"
                  rows="3"
                  placeholder="Template description"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Category</label>
                <select
                  value={newTemplate.category_id}
                  onChange={(e) => setNewTemplate({ ...newTemplate, category_id: e.target.value })}
                  className="form-input"
                >
                  <option value="">Select category</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>{category.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Content</label>
                <textarea
                  value={newTemplate.content}
                  onChange={(e) => setNewTemplate({ ...newTemplate, content: e.target.value })}
                  className="form-input"
                  rows="8"
                  placeholder="Template content with variables like {{customer_name}}"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Variables (comma-separated)</label>
                <input
                  type="text"
                  value={newTemplate.variables.join(', ')}
                  onChange={(e) => setNewTemplate({ ...newTemplate, variables: e.target.value.split(',').map(v => v.trim()).filter(v => v) })}
                  className="form-input"
                  placeholder="customer_name, date, amount"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Tags (comma-separated)</label>
                <input
                  type="text"
                  value={newTemplate.tags.join(', ')}
                  onChange={(e) => setNewTemplate({ ...newTemplate, tags: e.target.value.split(',').map(v => v.trim()).filter(v => v) })}
                  className="form-input"
                  placeholder="legal, contract, business"
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={createTemplate}
                className="flex-1 btn-primary"
                disabled={!newTemplate.title || !newTemplate.content}
              >
                Create Template
              </button>
              <button
                onClick={() => setShowTemplateModal(false)}
                className="flex-1 btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* File Conversion Modal */}
      {showConversionModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">Convert File</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Upload File</label>
                <input
                  type="file"
                  onChange={handleFileUpload}
                  className="form-input"
                  accept=".docx,.xlsx,.html,.txt"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">From</label>
                  <select
                    value={conversionRequest.source_format}
                    onChange={(e) => setConversionRequest({ ...conversionRequest, source_format: e.target.value })}
                    className="form-input"
                  >
                    <option value="docx">DOCX</option>
                    <option value="xlsx">XLSX</option>
                    <option value="html">HTML</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">To</label>
                  <select
                    value={conversionRequest.target_format}
                    onChange={(e) => setConversionRequest({ ...conversionRequest, target_format: e.target.value })}
                    className="form-input"
                  >
                    <option value="pdf">PDF</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Document Title</label>
                <input
                  type="text"
                  value={conversionRequest.document_title}
                  onChange={(e) => setConversionRequest({ ...conversionRequest, document_title: e.target.value })}
                  className="form-input"
                  placeholder="Optional title for converted file"
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={convertFile}
                className="flex-1 btn-primary"
                disabled={!conversionRequest.file_content}
              >
                Convert & Download
              </button>
              <button
                onClick={() => setShowConversionModal(false)}
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

export default DocumentCenter;