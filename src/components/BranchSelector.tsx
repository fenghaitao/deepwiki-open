import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, CodeBracketIcon } from '@heroicons/react/24/outline';

interface Branch {
  name: string;
  commit: {
    sha: string;
    url: string;
  };
}

interface BranchSelectorProps {
  owner: string;
  repo: string;
  repoType: 'github' | 'gitlab' | 'bitbucket';
  currentBranch: string;
  onBranchChange: (branch: string) => void;
  token?: string | null;
  className?: string;
}

export default function BranchSelector({
  owner,
  repo,
  repoType,
  currentBranch,
  onBranchChange,
  token,
  className = ""
}: BranchSelectorProps) {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch branches when component mounts or repo changes
  useEffect(() => {
    console.log('BranchSelector - Props:', { owner, repo, repoType, token: token ? 'present' : 'none' });
    if (owner && repo && owner !== '' && repo !== '') {
      fetchBranches();
    } else {
      console.log('BranchSelector - Skipping fetch due to missing owner/repo');
      setError('Repository information is incomplete');
    }
  }, [owner, repo, repoType, token]);

  const fetchBranches = async () => {
    console.log('BranchSelector - Fetching branches for:', { owner, repo, repoType });
    setIsLoading(true);
    setError(null);
    
    try {
      let apiUrl = '';
      const headers: Record<string, string> = {
        'Accept': 'application/json',
      };

      // Add authentication if token is provided
      if (token && token.trim() !== '') {
        if (repoType === 'github') {
          headers['Authorization'] = `token ${token}`;
        } else if (repoType === 'gitlab') {
          headers['PRIVATE-TOKEN'] = token;
        }
      }

      // Build API URL based on repo type
      switch (repoType) {
        case 'github':
          apiUrl = `https://api.github.com/repos/${owner}/${repo}/branches`;
          break;
        case 'gitlab':
          // Encode the project path for GitLab API
          const projectPath = encodeURIComponent(`${owner}/${repo}`);
          apiUrl = `https://gitlab.com/api/v4/projects/${projectPath}/repository/branches`;
          break;
        case 'bitbucket':
          apiUrl = `https://api.bitbucket.org/2.0/repositories/${owner}/${repo}/refs/branches`;
          if (token) {
            headers['Authorization'] = `Bearer ${token}`;
          }
          break;
        default:
          throw new Error(`Unsupported repository type: ${repoType}`);
      }

      const response = await fetch(apiUrl, { headers });
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Repository not found or no access');
        } else if (response.status === 403) {
          if (!token) {
            throw new Error('Repository requires authentication. Please add an access token.');
          } else {
            throw new Error('Access denied - check your token permissions');
          }
        } else if (response.status === 429) {
          throw new Error('Rate limit exceeded. Please try again later or add an access token.');
        } else {
          throw new Error(`Failed to fetch branches: ${response.statusText}`);
        }
      }

      const data = await response.json();
      
      // Normalize branch data across different APIs
      let normalizedBranches: Branch[] = [];
      
      if (repoType === 'github') {
        normalizedBranches = data.map((branch: any) => ({
          name: branch.name,
          commit: {
            sha: branch.commit.sha,
            url: branch.commit.url
          }
        }));
      } else if (repoType === 'gitlab') {
        normalizedBranches = data.map((branch: any) => ({
          name: branch.name,
          commit: {
            sha: branch.commit.id,
            url: branch.commit.web_url
          }
        }));
      } else if (repoType === 'bitbucket') {
        normalizedBranches = data.values.map((branch: any) => ({
          name: branch.name,
          commit: {
            sha: branch.target.hash,
            url: branch.target.links.html.href
          }
        }));
      }

      setBranches(normalizedBranches);
    } catch (err) {
      console.error('Error fetching branches:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch branches';
      setError(errorMessage);
      
      // Set some common default branches as fallback
      setBranches([
        { name: 'main', commit: { sha: 'unknown', url: '' } },
        { name: 'master', commit: { sha: 'unknown', url: '' } },
        { name: 'develop', commit: { sha: 'unknown', url: '' } }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBranchSelect = (branchName: string) => {
    onBranchChange(branchName);
    setIsOpen(false);
  };

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-1.5 px-2 py-0.5 bg-[var(--background)] 
                   border border-[var(--border-color)] rounded-full hover:bg-[var(--background-secondary)]
                   transition-colors text-sm"
        disabled={isLoading}
      >
        <CodeBracketIcon className="w-3 h-3" />
        <span className="truncate max-w-24">
          {isLoading ? 'Loading...' : currentBranch}
        </span>
        <ChevronDownIcon className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-64 bg-white dark:bg-gray-800 
                        border border-gray-300 dark:border-gray-600 rounded-md shadow-2xl z-[9999] max-h-64 overflow-y-auto">
          {error ? (
            <div className="p-3 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
              <div className="mb-2 text-red-700 dark:text-red-300 text-sm font-medium">{error}</div>
              <div className="flex gap-2 items-center">
                <button 
                  onClick={fetchBranches}
                  className="text-blue-600 dark:text-blue-400 hover:underline text-xs font-medium"
                >
                  Retry
                </button>
                <span className="text-gray-400 dark:text-gray-500 text-xs">•</span>
                <span className="text-gray-600 dark:text-gray-400 text-xs">Will use: {currentBranch}</span>
              </div>
            </div>
          ) : branches.length === 0 && !isLoading ? (
            <div className="p-3 bg-gray-50 dark:bg-gray-900/50">
              <div className="mb-1 text-gray-700 dark:text-gray-300 text-sm">No branches found</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">Using default: {currentBranch}</div>
            </div>
          ) : (
            <div className="py-1">
              {branches.map((branch) => (
                <button
                  key={branch.name}
                  onClick={() => handleBranchSelect(branch.name)}
                  className={`w-full text-left px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 
                             transition-colors text-sm ${
                               branch.name === currentBranch 
                                 ? 'bg-blue-500 text-white' 
                                 : 'text-gray-900 dark:text-gray-100'
                             }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="truncate font-medium">{branch.name}</span>
                    {branch.name === currentBranch && (
                      <span className="text-xs opacity-75 bg-white/20 px-1.5 py-0.5 rounded">current</span>
                    )}
                  </div>
                  {branch.commit.sha !== 'unknown' && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 truncate mt-1 font-mono">
                      {branch.commit.sha.substring(0, 7)}
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Click outside to close */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-[9998]" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
}