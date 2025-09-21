import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TeamManagement = () => {
  const [teamMembers, setTeamMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedDepartment, setSelectedDepartment] = useState('all');
  const [newMember, setNewMember] = useState({
    name: '',
    email: '',
    role: '',
    department: '',
    avatar_url: ''
  });

  useEffect(() => {
    fetchTeamMembers();
  }, []);

  const fetchTeamMembers = async () => {
    try {
      const response = await axios.get(`${API}/team`);
      setTeamMembers(response.data);
    } catch (error) {
      console.error('Error fetching team members:', error);
    } finally {
      setLoading(false);
    }
  };

  const createTeamMember = async () => {
    try {
      const response = await axios.post(`${API}/team`, newMember);
      setTeamMembers([response.data, ...teamMembers]);
      setNewMember({
        name: '',
        email: '',
        role: '',
        department: '',
        avatar_url: ''
      });
      setShowCreateModal(false);
    } catch (error) {
      console.error('Error creating team member:', error);
    }
  };

  const departments = ['all', ...new Set(teamMembers.map(member => member.department))];
  const filteredMembers = selectedDepartment === 'all' 
    ? teamMembers 
    : teamMembers.filter(member => member.department === selectedDepartment);

  const getDepartmentStats = () => {
    const stats = {};
    teamMembers.forEach(member => {
      if (!stats[member.department]) {
        stats[member.department] = { total: 0, online: 0 };
      }
      stats[member.department].total++;
      if (member.is_online) {
        stats[member.department].online++;
      }
    });
    return stats;
  };

  const departmentStats = getDepartmentStats();

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-48 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
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
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Team Management</h1>
          <p className="text-gray-600 dark:text-gray-400">Manage your team members and track performance</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Add Member
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Members</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{teamMembers.length}</p>
            </div>
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
              <span className="text-blue-600 dark:text-blue-400">👥</span>
            </div>
          </div>
        </div>
        
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Online Now</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {teamMembers.filter(m => m.is_online).length}
              </p>
            </div>
            <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
              <span className="text-green-600 dark:text-green-400">🟢</span>
            </div>
          </div>
        </div>

        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Departments</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {Object.keys(departmentStats).length}
              </p>
            </div>
            <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
              <span className="text-purple-600 dark:text-purple-400">🏢</span>
            </div>
          </div>
        </div>

        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Tasks</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {teamMembers.reduce((sum, m) => sum + (m.tasks_assigned || 0), 0)}
              </p>
            </div>
            <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
              <span className="text-orange-600 dark:text-orange-400">📋</span>
            </div>
          </div>
        </div>
      </div>

      {/* Department Filters */}
      <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-4 border border-gray-200/50 dark:border-gray-700/50 mb-6">
        <div className="flex flex-wrap gap-2">
          {departments.map((dept) => (
            <button
              key={dept}
              onClick={() => setSelectedDepartment(dept)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                selectedDepartment === dept
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              {dept === 'all' ? 'All Departments' : dept}
              {dept !== 'all' && departmentStats[dept] && (
                <span className="ml-1 text-xs">
                  ({departmentStats[dept].total})
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Team Members Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredMembers.map((member) => (
          <div key={member.id} className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50 card-hover">
            <div className="flex items-start space-x-4">
              <div className="relative">
                <img
                  src={member.avatar_url || `https://ui-avatars.com/api/?name=${encodeURIComponent(member.name)}&background=3b82f6&color=fff`}
                  alt={member.name}
                  className="w-16 h-16 rounded-full border-2 border-gray-200 dark:border-gray-600"
                />
                <div className={`absolute -bottom-1 -right-1 w-5 h-5 rounded-full border-2 border-white dark:border-gray-800 ${
                  member.is_online ? 'bg-green-400' : 'bg-gray-400'
                }`}></div>
              </div>
              
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                  {member.name}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                  {member.role}
                </p>
                <div className="flex items-center space-x-2 mt-1">
                  <span className="tag tag-blue">{member.department}</span>
                  <span className={`text-xs px-2 py-1 rounded-full ${
                    member.is_online 
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200'
                  }`}>
                    {member.is_online ? 'Online' : 'Offline'}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-200/50 dark:border-gray-700/50">
              <div className="grid grid-cols-2 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {member.tasks_assigned || 0}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Assigned</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {member.tasks_completed || 0}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Completed</p>
                </div>
              </div>
              
              <div className="mt-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-500 dark:text-gray-400">Completion Rate</span>
                  <span className="text-xs font-medium text-gray-900 dark:text-white">
                    {member.tasks_assigned ? Math.round((member.tasks_completed / member.tasks_assigned) * 100) : 0}%
                  </span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill"
                    style={{ 
                      width: `${member.tasks_assigned ? (member.tasks_completed / member.tasks_assigned) * 100 : 0}%` 
                    }}
                  ></div>
                </div>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-200/50 dark:border-gray-700/50">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500 dark:text-gray-400 truncate">
                  {member.email}
                </span>
                <div className="flex space-x-2">
                  <button className="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium">
                    Message
                  </button>
                  <button className="text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 font-medium">
                    Profile
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredMembers.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">👥</div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">No team members found</h3>
          <p className="text-gray-600 dark:text-gray-400">
            {selectedDepartment === 'all' ? 'Add your first team member to get started' : `No members in ${selectedDepartment} department`}
          </p>
        </div>
      )}

      {/* Create Member Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Add Team Member</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
                <input
                  type="text"
                  value={newMember.name}
                  onChange={(e) => setNewMember({ ...newMember, name: e.target.value })}
                  className="form-input"
                  placeholder="Enter member name"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                <input
                  type="email"
                  value={newMember.email}
                  onChange={(e) => setNewMember({ ...newMember, email: e.target.value })}
                  className="form-input"
                  placeholder="Enter email address"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Role</label>
                <input
                  type="text"
                  value={newMember.role}
                  onChange={(e) => setNewMember({ ...newMember, role: e.target.value })}
                  className="form-input"
                  placeholder="Enter role/position"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Department</label>
                <select
                  value={newMember.department}
                  onChange={(e) => setNewMember({ ...newMember, department: e.target.value })}
                  className="form-input"
                >
                  <option value="">Select department</option>
                  <option value="Sales">Sales</option>
                  <option value="Marketing">Marketing</option>
                  <option value="Engineering">Engineering</option>
                  <option value="Product">Product</option>
                  <option value="Support">Support</option>
                  <option value="HR">HR</option>
                  <option value="Finance">Finance</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Avatar URL (Optional)</label>
                <input
                  type="url"
                  value={newMember.avatar_url}
                  onChange={(e) => setNewMember({ ...newMember, avatar_url: e.target.value })}
                  className="form-input"
                  placeholder="Enter avatar image URL"
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={createTeamMember}
                className="flex-1 btn-primary"
                disabled={!newMember.name || !newMember.email || !newMember.role || !newMember.department}
              >
                Add Member
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

export default TeamManagement;