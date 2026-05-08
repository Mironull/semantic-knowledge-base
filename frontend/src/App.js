import React, { useState } from 'react';

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [isAdminOpen, setIsAdminOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  // --- НОВЫЕ СОСТОЯНИЯ ---
  const [searchHistory, setSearchHistory] = useState([]); // История поисков
  const [uploadFiles, setUploadFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState('');
  const [uploadProgress, setUploadProgress] = useState({});
  const [error, setError] = useState('');
  const [allDocuments, setAllDocuments] = useState([]);
  const [isDocumentsOpen, setIsDocumentsOpen] = useState(false);
  const [previewDoc, setPreviewDoc] = useState(null);
  const [previewContent, setPreviewContent] = useState('');
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [sortBy, setSortBy] = useState('date');
  const [sortDir, setSortDir] = useState('desc');
  const [reembedAllStatus, setReembedAllStatus] = useState('');

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

  const startVoiceRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Ваш браузер не поддерживает голосовой ввод.");
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = 'ru-RU';
    recognition.start();
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setSearchQuery(transcript);
      handleSearch(transcript); // Сразу запускаем поиск
    };
  };

  const theme = {
    bg: isDarkMode ? '#0f172a' : '#f8fafc',
    bgGradients: isDarkMode
      ? 'radial-gradient(at 0% 0%, rgba(224, 142, 180, 0.1) 0px, transparent 50%)'
      : 'radial-gradient(at 0% 0%, rgba(224, 142, 180, 0.08) 0px, transparent 50%)',
    card: isDarkMode ? '#1e293b' : '#ffffff',
    cardBorder: isDarkMode ? '#334155' : '#e2e8f0',
    textMain: isDarkMode ? '#f1f5f9' : '#1e293b',
    textPink: '#e08eb4',
    textSub: isDarkMode ? '#94a3b8' : '#64748b',
    textResultsTag: isDarkMode ? '#cbd5e1' : '#94a3b8',
    btnBg: '#e08eb4',
    tagBg: isDarkMode ? 'rgba(224, 142, 180, 0.08)' : 'rgba(224, 142, 180, 0.05)',
    tagBorder: isDarkMode ? '#334155' : '#f1f5f9',
    tagText: isDarkMode ? '#eab0cc' : '#c27699',
    shadow: isDarkMode ? '0 20px 25px -5px rgba(0, 0, 0, 0.2)' : '0 20px 25px -5px rgba(0, 0, 0, 0.05)'
  };

  const baseStyle = {
    fontFamily: '"Inter", sans-serif',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
  };

  // Поиск документов через backend API
  const handleSearch = async (queryOverride) => {
    const finalQuery = typeof queryOverride === 'string' ? queryOverride : searchQuery;
    if (!finalQuery.trim()) return;

    setIsLoading(true);
    setHasSearched(false);
    setError('');

    // Добавляем в историю (только уникальные значения, максимум 5)
    setSearchHistory(prev => {
      const filtered = prev.filter(item => item !== finalQuery);
      return [finalQuery, ...filtered].slice(0, 5);
    });

    try {
      const response = await fetch(`${API_BASE_URL}/search?name=${encodeURIComponent(finalQuery)}`);
      if (!response.ok) {
        throw new Error('Ошибка поиска');
      }
      const data = await response.json();

      const formattedResults = data.map(doc => ({
        id: doc.id,
        title: doc.filename,
        meta: `${doc.content_type} • ${new Date(doc.upload_date).toLocaleString('ru-RU')}`,
        downloadUrl: `${API_BASE_URL}/download/${doc.id}`,
        similarity: doc.similarity_score,
        chunkText: doc.chunk_text || null,
        chunkIndex: doc.chunk_index ?? null,
      }));

      setResults(formattedResults);
      setHasSearched(true);
    } catch (err) {
      setError('Не удалось выполнить поиск. Убедитесь, что backend запущен.');
      setResults([]);
      setHasSearched(true);
    } finally {
      setIsLoading(false);
    }
  };

  // Загрузка документов
  const handleFileUpload = async () => {
    if (uploadFiles.length === 0) return;

    setUploadStatus('Загрузка...');
    setError('');

    const initial = {};
    uploadFiles.forEach(f => { initial[f.name] = 'pending'; });
    setUploadProgress(initial);

    let successCount = 0;
    for (const file of uploadFiles) {
      setUploadProgress(prev => ({ ...prev, [file.name]: 'uploading' }));
      try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await fetch(`${API_BASE_URL}/upload`, { method: 'POST', body: formData });
        if (!response.ok) throw new Error();
        setUploadProgress(prev => ({ ...prev, [file.name]: 'done' }));
        successCount++;
      } catch {
        setUploadProgress(prev => ({ ...prev, [file.name]: 'error' }));
      }
    }

    loadAllDocuments();
    setUploadStatus(`Загружено ${successCount} из ${uploadFiles.length}`);
    setTimeout(() => {
      setUploadFiles([]);
      setUploadProgress({});
      setUploadStatus('');
    }, 3000);
  };

  // Загрузка всех документов
  const loadAllDocuments = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/documents`);
      if (!response.ok) throw new Error('Ошибка загрузки');
      const data = await response.json();
      setAllDocuments(data);
    } catch (err) {
      setError('Не удалось загрузить список документов');
    }
  };

  // Предпросмотр документа
  const handlePreview = async (docId, docName) => {
    setPreviewDoc({ id: docId, name: docName });
    setIsPreviewLoading(true);
    setPreviewContent('');

    try {
      const response = await fetch(`${API_BASE_URL}/preview/${docId}`);
      if (!response.ok) throw new Error('Ошибка предпросмотра');
      const data = await response.json();

      if (data.type === 'text') {
        setPreviewContent(data.content);
      } else {
        setPreviewContent(data.content || 'Предпросмотр недоступен для данного типа файла');
      }
    } catch (err) {
      setPreviewContent('Не удалось загрузить предпросмотр');
    } finally {
      setIsPreviewLoading(false);
    }
  };

  // Удаление документа
  const handleDelete = async (docId, docName) => {
    if (!window.confirm(`Удалить «${docName}»?`)) return;
    try {
      const response = await fetch(`${API_BASE_URL}/documents/${docId}`, { method: 'DELETE' });
      if (!response.ok) throw new Error('Ошибка удаления');
      setAllDocuments(prev => prev.filter(d => d.id !== docId));
      setResults(prev => prev.filter(r => r.id !== docId));
    } catch (err) {
      setError('Не удалось удалить документ.');
    }
  };

  // Закрыть предпросмотр
  const closePreview = () => {
    setPreviewDoc(null);
    setPreviewContent('');
  };

  // Пересоздать эмбеддинги для всех документов
  const handleReembedAll = async () => {
    setReembedAllStatus('loading');
    try {
      const response = await fetch(`${API_BASE_URL}/reembed-all`, { method: 'POST' });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Ошибка');
      }
      const data = await response.json();
      setReembedAllStatus(`Готово: ${data.ok} из ${data.total}`);
    } catch (err) {
      setReembedAllStatus('Ошибка пересоздания');
    }
    setTimeout(() => setReembedAllStatus(''), 5000);
  };

  // Загружаем все документы при открытии панели
  const toggleDocuments = () => {
    if (!isDocumentsOpen) {
      loadAllDocuments();
    }
    setIsDocumentsOpen(!isDocumentsOpen);
  };

  const sortedDocuments = [...allDocuments].sort((a, b) => {
    let cmp = 0;
    if (sortBy === 'name') cmp = a.filename.localeCompare(b.filename);
    else if (sortBy === 'size') cmp = a.size - b.size;
    else cmp = new Date(a.upload_date) - new Date(b.upload_date);
    return sortDir === 'asc' ? cmp : -cmp;
  });

  const handleSort = (field) => {
    if (sortBy === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortBy(field); setSortDir('asc'); }
  };

  // Форматирование размера файла
  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <div style={{
      ...baseStyle,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      minHeight: '100vh',
      width: '100%',
      backgroundColor: theme.bg,
      backgroundImage: theme.bgGradients,
      padding: '20px',
      paddingTop: '5vh',
      boxSizing: 'border-box',
      position: 'relative',
    }}>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body { margin: 0; padding: 0; background-color: ${theme.bg}; overflow-x: hidden; -webkit-font-smoothing: antialiased; }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* Анимация пульсации для Скелетона */
        @keyframes skeletonPulse {
          0% { opacity: 0.6; }
          50% { opacity: 1; }
          100% { opacity: 0.6; }
        }
      `}</style>

      {/* КНОПКА ТЕМЫ */}
      <button
        onClick={() => setIsDarkMode(!isDarkMode)}
        style={{
          ...baseStyle,
          position: 'absolute', top: '20px', right: '20px', width: '44px', height: '44px', borderRadius: '50%',
          border: `1px solid ${theme.cardBorder}`, backgroundColor: theme.card, color: theme.textMain,
          cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 10,
          boxShadow: theme.shadow, padding: 0
        }}
      >
        {isDarkMode ? (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5" /><line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" /><line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" /><line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" /><line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" /></svg>
        ) : (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>
        )}
      </button>

      <div style={{ width: '100%', maxWidth: '800px' }}>
        <header style={{ textAlign: 'center', marginBottom: '60px' }}>
          <h1 style={{
            ...baseStyle, fontSize: '68px', fontWeight: '600', letterSpacing: '-0.04em', lineHeight: '0.9',
            marginBottom: '20px', background: `linear-gradient(135deg, ${theme.textPink} 0%, #7d3c58 100%)`,
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', display: 'inline-block'
          }}>
            Semantic Search
          </h1>
          <p style={{ ...baseStyle, fontSize: '18px', color: theme.textSub, maxWidth: '500px', margin: '0 auto' }}>
            Интеллектуальный поиск по базе знаний компании.
          </p>
        </header>

        {/* ОШИБКА */}
        {error && (
          <div style={{
            ...baseStyle, backgroundColor: '#fee2e2', border: '1px solid #ef4444',
            color: '#dc2626', padding: '12px 20px', borderRadius: '12px', marginBottom: '16px',
            animation: 'fadeIn 0.3s'
          }}>
            {error}
          </div>
        )}

        {/* ПАНЕЛЬ ПОИСКА */}
        <div style={{
          ...baseStyle, display: 'flex', gap: '12px', backgroundColor: theme.card, padding: '8px',
          borderRadius: '24px', boxShadow: theme.shadow, marginBottom: '16px', border: `1px solid ${theme.cardBorder}`,
          alignItems: 'center'
        }}>
          <button onClick={startVoiceRecognition} style={{ background: 'none', border: 'none', cursor: 'pointer', paddingLeft: '18px', display: 'flex', alignItems: 'center', opacity: 0.5, color: theme.textMain }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><line x1="12" x2="12" y1="19" y2="22" /></svg>
          </button>
          <input
            type="text"
            placeholder="Спросите что-нибудь..."
            style={{ ...baseStyle, flex: 1, padding: '16px 12px', border: 'none', outline: 'none', fontSize: '16px', backgroundColor: 'transparent', color: theme.textMain }}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch} style={{ ...baseStyle, backgroundColor: theme.btnBg, color: 'white', padding: '12px 32px', borderRadius: '18px', border: 'none', fontWeight: '600', cursor: 'pointer' }}>
            {isLoading ? '...' : 'Найти'}
          </button>
        </div>

        {/* НЕДАВНИЕ ПОИСКИ */}
        {searchHistory.length > 0 && !isLoading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px', paddingLeft: '8px', animation: 'fadeIn 0.3s' }}>
            <span style={{ fontSize: '12px', color: theme.textResultsTag, fontWeight: '700', textTransform: 'uppercase' }}>История:</span>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {searchHistory.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => { setSearchQuery(item); handleSearch(item); }}
                  style={{ ...baseStyle, fontSize: '12px', border: 'none', background: 'none', color: theme.textPink, cursor: 'pointer', padding: '2px 4px', textDecoration: 'underline' }}
                >
                  {item}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* СКЕЛЕТОНЫ ПРИ ЗАГРУЗКЕ */}
        {isLoading && (
          <div style={{ width: '100%', animation: 'fadeIn 0.3s' }}>
            <div style={{ width: '150px', height: '12px', backgroundColor: theme.tagBg, marginBottom: '20px', borderRadius: '4px' }} />
            {[1, 2].map(i => (
              <div key={i} style={{
                backgroundColor: theme.card, padding: '24px', borderRadius: '24px', marginBottom: '16px',
                border: `1px solid ${theme.cardBorder}`, animation: 'skeletonPulse 1.5s infinite ease-in-out'
              }}>
                <div style={{ width: '40%', height: '20px', backgroundColor: theme.tagBg, borderRadius: '6px', marginBottom: '12px' }} />
                <div style={{ width: '90%', height: '14px', backgroundColor: theme.tagBg, borderRadius: '4px', marginBottom: '8px' }} />
                <div style={{ width: '70%', height: '14px', backgroundColor: theme.tagBg, borderRadius: '4px' }} />
              </div>
            ))}
          </div>
        )}

        {/* ТЕГИ (ПОПУЛЯРНЫЕ ЗАПРОСЫ) */}
        {!isLoading && !hasSearched && (
          <div style={{ display: 'flex', gap: '8px', marginBottom: '48px', flexWrap: 'wrap', justifyContent: 'center' }}>
            {['Отпуск', 'Больничный', 'ДМС', 'Парковка'].map(tag => (
              <button key={tag} onClick={() => { setSearchQuery(tag); handleSearch(tag); }} style={{ ...baseStyle, fontSize: '13px', fontWeight: '600', backgroundColor: theme.tagBg, border: `1px solid ${theme.tagBorder}`, color: theme.tagText, padding: '6px 16px', borderRadius: '99px', cursor: 'pointer' }}>
                {tag}
              </button>
            ))}
          </div>
        )}

        {/* ВСЕ ДОКУМЕНТЫ */}
        <div style={{ ...baseStyle, backgroundColor: theme.card, borderRadius: '24px', border: `1px solid ${theme.cardBorder}`, boxShadow: theme.shadow, marginBottom: '16px', overflow: 'hidden', padding: '8px' }}>
          <button onClick={toggleDocuments} style={{ ...baseStyle, width: '100%', padding: '12px 0', border: 'none', background: 'none', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', fontWeight: '500', color: theme.textMain }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ paddingLeft: '18px', display: 'flex', alignItems: 'center', opacity: 0.5 }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"/></svg>
              </div>
              <span style={{ fontSize: '16px', opacity: 0.7 }}>Все документы {allDocuments.length > 0 && `(${allDocuments.length})`}</span>
            </div>
            <div style={{ paddingRight: '18px', opacity: 0.3, transform: isDocumentsOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: '0.3s' }}>▼</div>
          </button>
          {isDocumentsOpen && (
            <div style={{ padding: '16px', borderTop: `1px solid ${theme.cardBorder}`, marginTop: '8px' }}>
              {allDocuments.length > 0 && (
                <div style={{ display: 'flex', gap: '6px', marginBottom: '12px', alignItems: 'center' }}>
                  <span style={{ fontSize: '12px', color: theme.textSub, fontWeight: '600', marginRight: '4px' }}>Сортировка:</span>
                  {[['name', 'По имени'], ['date', 'По дате'], ['size', 'По размеру']].map(([field, label]) => (
                    <button
                      key={field}
                      onClick={() => handleSort(field)}
                      style={{
                        ...baseStyle, fontSize: '12px', padding: '4px 10px', borderRadius: '8px', border: `1px solid ${theme.cardBorder}`,
                        cursor: 'pointer', fontWeight: sortBy === field ? '700' : '500',
                        backgroundColor: sortBy === field ? theme.btnBg : theme.tagBg,
                        color: sortBy === field ? 'white' : theme.tagText,
                        display: 'inline-flex', alignItems: 'center', gap: '4px'
                      }}
                    >
                      {label}
                      {sortBy === field && (sortDir === 'asc' ? ' ↑' : ' ↓')}
                    </button>
                  ))}
                </div>
              )}
              <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {allDocuments.length === 0 ? (
                <p style={{ color: theme.textSub, textAlign: 'center', padding: '20px' }}>Документы отсутствуют</p>
              ) : (
                sortedDocuments.map((doc) => (
                  <div key={doc.id} style={{ ...baseStyle, padding: '12px', marginBottom: '8px', backgroundColor: isDarkMode ? 'rgba(0,0,0,0.2)' : 'rgba(255,255,255,0.5)', borderRadius: '12px', border: `1px solid ${theme.cardBorder}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                      <h4 style={{ fontSize: '15px', fontWeight: '600', color: theme.textMain, margin: 0 }}>{doc.filename}</h4>
                      <span style={{ fontSize: '12px', color: theme.textSub }}>{formatSize(doc.size)}</span>
                    </div>
                    <p style={{ fontSize: '13px', color: theme.textSub, margin: '4px 0' }}>
                      {doc.content_type} • {new Date(doc.upload_date).toLocaleDateString('ru-RU')}
                    </p>
                    <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                      <button
                        onClick={() => handlePreview(doc.id, doc.filename)}
                        style={{ ...baseStyle, display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '13px', backgroundColor: theme.tagBg, color: theme.tagText, padding: '6px 12px', borderRadius: '8px', border: `1px solid ${theme.tagBorder}`, cursor: 'pointer', fontWeight: '600' }}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                        Просмотр
                      </button>
                      <a
                        href={`${API_BASE_URL}/download/${doc.id}`}
                        download
                        style={{ ...baseStyle, display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '13px', backgroundColor: theme.tagBg, color: theme.tagText, padding: '6px 12px', borderRadius: '8px', border: `1px solid ${theme.tagBorder}`, textDecoration: 'none', fontWeight: '600' }}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                        Скачать
                      </a>
                      <button
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        style={{ ...baseStyle, display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '13px', backgroundColor: 'rgba(239,68,68,0.08)', color: '#ef4444', padding: '6px 12px', borderRadius: '8px', border: '1px solid rgba(239,68,68,0.2)', cursor: 'pointer', fontWeight: '600' }}
                      >
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
                        Удалить
                      </button>
                    </div>
                  </div>
                ))
              )}
              </div>
            </div>
          )}
        </div>

        {/* УПРАВЛЕНИЕ БАЗОЙ */}
        <div style={{ ...baseStyle, backgroundColor: theme.card, borderRadius: '24px', border: `1px solid ${theme.cardBorder}`, boxShadow: theme.shadow, marginBottom: '40px', overflow: 'hidden', padding: '8px' }}>
          <button onClick={() => setIsAdminOpen(!isAdminOpen)} style={{ ...baseStyle, width: '100%', padding: '12px 0', border: 'none', background: 'none', display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', fontWeight: '500', color: theme.textMain }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ paddingLeft: '18px', display: 'flex', alignItems: 'center', opacity: 0.5 }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.1a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" /><circle cx="12" cy="12" r="3" /></svg>
              </div>
              <span style={{ fontSize: '16px', opacity: 0.7 }}>Управление базой знаний</span>
            </div>
            <div style={{ paddingRight: '18px', opacity: 0.3, transform: isAdminOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: '0.3s' }}>▼</div>
          </button>
          {isAdminOpen && (
            <div style={{ padding: '24px', borderTop: `1px solid ${theme.cardBorder}`, marginTop: '8px' }}>
              <div style={{ border: isDarkMode ? '2px dashed #475569' : '2px dashed #cbd5e1', borderRadius: '20px', padding: '30px', textAlign: 'center', backgroundColor: isDarkMode ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.4)' }}>
                <p style={{ color: theme.textSub, fontSize: '14px', marginBottom: '16px' }}>Загрузите PDF, Word или текстовые документы</p>
                <input
                  type="file"
                  multiple
                  onChange={(e) => { setUploadFiles(Array.from(e.target.files)); setUploadProgress({}); setUploadStatus(''); }}
                  style={{ fontSize: '14px', color: theme.textSub, marginBottom: '16px' }}
                />
                {uploadFiles.length > 0 && (
                  <div style={{ textAlign: 'left', marginTop: '12px', marginBottom: '12px' }}>
                    {uploadFiles.map(f => {
                      const st = uploadProgress[f.name];
                      const icon = st === 'done' ? '✓' : st === 'error' ? '✗' : st === 'uploading' ? '…' : '·';
                      const color = st === 'done' ? '#10b981' : st === 'error' ? '#ef4444' : theme.textSub;
                      return (
                        <div key={f.name} style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 0', borderBottom: `1px solid ${theme.cardBorder}` }}>
                          <span style={{ fontWeight: '700', color, minWidth: '14px', textAlign: 'center' }}>{icon}</span>
                          <span style={{ fontSize: '13px', color: theme.textMain, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</span>
                          <span style={{ fontSize: '12px', color: theme.textSub, flexShrink: 0 }}>{formatSize(f.size)}</span>
                        </div>
                      );
                    })}
                  </div>
                )}
                {uploadFiles.length > 0 && !uploadStatus && (
                  <button
                    onClick={handleFileUpload}
                    style={{
                      ...baseStyle, backgroundColor: theme.btnBg, color: 'white',
                      padding: '10px 24px', borderRadius: '12px', border: 'none',
                      fontWeight: '600', cursor: 'pointer', marginTop: '8px'
                    }}
                  >
                    Загрузить {uploadFiles.length > 1 ? `(${uploadFiles.length} файла)` : ''}
                  </button>
                )}
                {uploadStatus && (
                  <p style={{ color: theme.textPink, fontSize: '14px', marginTop: '12px', fontWeight: '500' }}>
                    {uploadStatus}
                  </p>
                )}
              </div>
              <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: `1px solid ${theme.cardBorder}`, display: 'flex', alignItems: 'center', gap: '12px' }}>
                <button
                  onClick={handleReembedAll}
                  disabled={reembedAllStatus === 'loading'}
                  style={{ ...baseStyle, display: 'inline-flex', alignItems: 'center', gap: '8px', backgroundColor: theme.tagBg, color: theme.tagText, padding: '10px 20px', borderRadius: '12px', border: `1px solid ${theme.tagBorder}`, cursor: reembedAllStatus === 'loading' ? 'wait' : 'pointer', fontWeight: '600', fontSize: '14px' }}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/></svg>
                  {reembedAllStatus === 'loading' ? 'Пересоздание...' : 'Пересоздать все эмбеддинги'}
                </button>
                {reembedAllStatus && reembedAllStatus !== 'loading' && (
                  <span style={{ fontSize: '13px', color: reembedAllStatus.startsWith('Готово') ? '#10b981' : '#ef4444', fontWeight: '600' }}>
                    {reembedAllStatus}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>

        {/* РЕЗУЛЬТАТЫ */}
        <div style={{ width: '100%' }}>
          {hasSearched && !isLoading && (
            <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
              <h2 style={{ fontSize: '12px', fontWeight: '800', color: theme.textResultsTag, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: '16px', marginLeft: '4px' }}>
                Найденные соответствия ({results.length})
              </h2>
              {results.length === 0 ? (
                <div style={{ ...baseStyle, backgroundColor: theme.card, padding: '40px', borderRadius: '24px', border: `1px solid ${theme.cardBorder}`, textAlign: 'center' }}>
                  <p style={{ color: theme.textSub, fontSize: '16px' }}>Документы не найдены</p>
                </div>
              ) : (
                results.map((item) => (
                  <div key={item.id} style={{ ...baseStyle, backgroundColor: theme.card, padding: '24px', borderRadius: '24px', marginBottom: '16px', border: `1px solid ${theme.cardBorder}`, boxShadow: isDarkMode ? 'none' : '0 4px 6px -1px rgba(0, 0, 0, 0.05)', position: 'relative' }}>
                    {/* Similarity Badge */}
                    {item.similarity !== null && item.similarity !== undefined && (
                      <div style={{
                        position: 'absolute',
                        top: '16px',
                        right: '16px',
                        backgroundColor: item.similarity >= 0.7 ? '#10b981' : item.similarity >= 0.5 ? '#f59e0b' : '#6b7280',
                        color: 'white',
                        padding: '6px 12px',
                        borderRadius: '12px',
                        fontSize: '13px',
                        fontWeight: '700',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px'
                      }}>
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                        </svg>
                        {(item.similarity * 100).toFixed(0)}%
                      </div>
                    )}
                    <h3 style={{ fontSize: '20px', fontWeight: '700', color: theme.textMain, marginBottom: '4px', paddingRight: item.similarity ? '100px' : '0' }}>{item.title}</h3>
                    <p style={{ color: theme.textSub, fontSize: '12px', marginBottom: '10px', marginTop: 0 }}>{item.meta}</p>
                    {item.chunkText && (
                      <div style={{
                        backgroundColor: isDarkMode ? 'rgba(224,142,180,0.06)' : 'rgba(224,142,180,0.06)',
                        border: `1px solid ${isDarkMode ? 'rgba(224,142,180,0.18)' : 'rgba(224,142,180,0.2)'}`,
                        borderRadius: '10px', padding: '10px 14px', marginBottom: '12px'
                      }}>
                        {item.chunkIndex !== null && (
                          <span style={{ fontSize: '11px', fontWeight: '700', color: theme.textPink, textTransform: 'uppercase', letterSpacing: '0.05em', display: 'block', marginBottom: '4px' }}>
                            Фрагмент #{item.chunkIndex + 1}
                          </span>
                        )}
                        <p style={{ color: theme.textMain, fontSize: '14px', lineHeight: '1.6', margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                          {item.chunkText.length > 400 ? item.chunkText.slice(0, 400) + '…' : item.chunkText}
                        </p>
                      </div>
                    )}
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => handlePreview(item.id, item.title)}
                        style={{
                          ...baseStyle, display: 'inline-flex', alignItems: 'center', gap: '8px',
                          backgroundColor: theme.tagBg, color: theme.tagText, padding: '8px 16px',
                          borderRadius: '12px', border: `1px solid ${theme.tagBorder}`,
                          cursor: 'pointer', fontSize: '14px', fontWeight: '600'
                        }}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
                          <circle cx="12" cy="12" r="3"/>
                        </svg>
                        Просмотр
                      </button>
                      <a
                        href={item.downloadUrl}
                        download
                        style={{
                          ...baseStyle, display: 'inline-flex', alignItems: 'center', gap: '8px',
                          backgroundColor: theme.tagBg, color: theme.tagText, padding: '8px 16px',
                          borderRadius: '12px', border: `1px solid ${theme.tagBorder}`,
                          textDecoration: 'none', fontSize: '14px', fontWeight: '600'
                        }}
                      >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                          <polyline points="7 10 12 15 17 10" />
                          <line x1="12" y1="15" x2="12" y2="3" />
                        </svg>
                        Скачать
                      </a>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* МОДАЛЬНОЕ ОКНО ПРЕДПРОСМОТРА */}
      {previewDoc && (
        <div
          onClick={closePreview}
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.75)', display: 'flex',
            justifyContent: 'center', alignItems: 'center', zIndex: 1000,
            padding: '20px', animation: 'fadeIn 0.2s'
          }}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              ...baseStyle, backgroundColor: theme.card, borderRadius: '24px',
              maxWidth: '900px', width: '100%', maxHeight: '80vh',
              display: 'flex', flexDirection: 'column', overflow: 'hidden',
              border: `1px solid ${theme.cardBorder}`, boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)'
            }}
          >
            {/* Заголовок модального окна */}
            <div style={{ padding: '20px', borderBottom: `1px solid ${theme.cardBorder}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', color: theme.textMain, margin: 0 }}>{previewDoc.name}</h3>
              <button
                onClick={closePreview}
                style={{
                  ...baseStyle, background: 'none', border: 'none', fontSize: '24px',
                  cursor: 'pointer', color: theme.textSub, padding: '0 8px'
                }}
              >
                ✕
              </button>
            </div>

            {/* Контент предпросмотра */}
            <div style={{ padding: '20px', overflowY: 'auto', flex: 1 }}>
              {isPreviewLoading ? (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <div style={{ animation: 'skeletonPulse 1.5s infinite ease-in-out' }}>
                    <p style={{ color: theme.textSub }}>Загрузка...</p>
                  </div>
                </div>
              ) : (
                <pre style={{
                  whiteSpace: 'pre-wrap', wordWrap: 'break-word',
                  fontFamily: '"Courier New", monospace', fontSize: '14px',
                  color: theme.textMain, margin: 0, lineHeight: '1.6'
                }}>
                  {previewContent}
                </pre>
              )}
            </div>

            {/* Кнопка закрытия снизу */}
            <div style={{ padding: '16px', borderTop: `1px solid ${theme.cardBorder}`, textAlign: 'center' }}>
              <button
                onClick={closePreview}
                style={{
                  ...baseStyle, backgroundColor: theme.btnBg, color: 'white',
                  padding: '10px 24px', borderRadius: '12px', border: 'none',
                  fontWeight: '600', cursor: 'pointer'
                }}
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;