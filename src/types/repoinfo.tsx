export interface RepoInfo {
    owner: string;
    repo: string;
    type: string;
    token: string | null;
    localPath: string | null;
    repoUrl: string | null;
    branch?: string; // Optional branch parameter
}

export default RepoInfo;