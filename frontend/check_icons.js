const l = require('lucide-react');
const keys = Object.keys(l);
const wifi = keys.filter(k => k.toLowerCase().includes('wifi') || k.toLowerCase().includes('signal') || k.toLowerCase().includes('thermometer') || k.toLowerCase().includes('flame'));
console.log('Wifi/Signal/Thermometer/Flame:', wifi.join(', '));
