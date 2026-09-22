// Logger mínimo e configurável (sem dependência externa): centraliza o formato
// de log e permite ajustar/silenciar por nível via LOG_LEVEL, em vez de cada
// módulo chamar console.log/console.error diretamente para eventos de negócio.
const LEVELS = { error: 0, info: 1, debug: 2 };

const currentLevel = LEVELS[process.env.LOG_LEVEL] !== undefined ? process.env.LOG_LEVEL : 'info';

function log(levelName, message) {
  if (LEVELS[levelName] > LEVELS[currentLevel]) return;
  const out = levelName === 'error' ? console.error : console.log;
  out(`[${levelName.toUpperCase()}] ${message}`);
}

module.exports = {
  info: (message) => log('info', message),
  error: (message) => log('error', message),
  debug: (message) => log('debug', message),
};
