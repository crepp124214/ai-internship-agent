// frontend/src/pages/components/DataImportModal.tsx
import React, { useState } from 'react';

interface DataImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess?: () => void;
}

export const DataImportModal: React.FC<DataImportModalProps> = ({
  isOpen,
  onClose,
  onImportSuccess,
}) => {
  const [activeTab, setActiveTab] = useState<'resume' | 'jd'>('resume');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const endpoint = activeTab === 'resume'
        ? '/api/v1/import/resume'
        : '/api/v1/import/jds';

      const token = localStorage.getItem('token');
      const headers: Record<string, string> = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
        headers,
      });

      const data = await response.json();
      setResult(data);

      if (data.success && onImportSuccess) {
        onImportSuccess();
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-md p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">导入数据</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        <div className="flex gap-2 mb-4">
          <button
            className={`px-4 py-2 rounded ${
              activeTab === 'resume'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 hover:bg-gray-300'
            }`}
            onClick={() => setActiveTab('resume')}
          >
            简历导入
          </button>
          <button
            className={`px-4 py-2 rounded ${
              activeTab === 'jd'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 hover:bg-gray-300'
            }`}
            onClick={() => setActiveTab('jd')}
          >
            JD 批量导入
          </button>
        </div>

        <div className="mb-4">
          <input
            type="file"
            accept={activeTab === 'resume' ? '.pdf,.docx' : '.csv,.xlsx'}
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-50 file:text-blue-700
              hover:file:bg-blue-100"
          />
          <p className="text-xs text-gray-500 mt-1">
            {activeTab === 'resume'
              ? '支持 PDF、DOCX 格式'
              : '支持 CSV、Excel 格式'}
          </p>
        </div>

        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="w-full py-2 px-4 bg-blue-500 text-white rounded
                     hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          {uploading ? '上传中...' : '上传'}
        </button>

        {error && (
          <div className="mt-4 p-3 bg-red-100 rounded text-red-700">
            {error}
          </div>
        )}

        {result && (
          <div className={`mt-4 p-3 rounded ${
            result.success ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            {result.success ? (
              <div>
                <p className="font-semibold">导入成功！</p>
                {activeTab === 'resume' ? (
                  <p>简历 ID: {result.resume_id}</p>
                ) : (
                  <p>
                    成功导入 {result.imported}/{result.total} 条
                    {result.failed > 0 && `（失败 {result.failed} 条）`}
                  </p>
                )}
                {result.parsed && (
                  <div className="mt-2 text-sm">
                    <p>姓名: {result.parsed.name}</p>
                    <p>学历: {result.parsed.education}</p>
                    <p>技能: {result.parsed.skills?.join(', ')}</p>
                  </div>
                )}
              </div>
            ) : (
              <p>导入失败：{result.detail || result.error}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
