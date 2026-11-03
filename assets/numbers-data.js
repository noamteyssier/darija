const UNITS = [null, ['wa7ed', 'واحد'], ['juj', 'جوج'], ['tlata', 'تلاتة'], ['rb3a', 'ربعة'], ['khamsa', 'خمسة'], ['setta', 'ستة'], ['sb3a', 'سبعة'], ['tmanya', 'تمنية'], ['ts3ud', 'تسعود'],
  ['3achra', 'عشرة'], ['7dach', 'حداش'], ['tnach', 'طناش'], ['tlettach', 'تلطاش'], ['rb3tach', 'ربعطاش'], ['khamstach', 'خمسطاش'], ['settach', 'سطاش'], ['sb3tach', 'سبعطاش'], ['tmentach', 'تمنطاش'], ['ts3tach', 'تسعطاش']];
const TENS = [null, null, ['3achrin', 'عشرين'], ['tlatin', 'تلاتين'], ['rb3in', 'ربعين'], ['khamsin', 'خمسين'], ['settin', 'ستين'], ['sb3in', 'سبعين'], ['tmanin', 'تمانين'], ['ts3in', 'تسعين']];
// Hundreds from 300 and thousands from 3000 use these short stems: tlt mya, tlt alaf.
const STEM = { 3: ['tlt', 'تلت'], 4: ['rb3', 'ربع'], 5: ['khms', 'خمس'], 6: ['stt', 'ست'], 7: ['sb3', 'سبع'], 8: ['tmn', 'تمن'], 9: ['ts3', 'تسع'], 10: ['3achr', 'عشر'] };

// 0 to 10000. Parts (thousands, hundreds, then units and tens) are joined with "w" (and).
export function say(n) {
  if (!n) return { lat: 'sifr', ar: 'صفر' };
  const parts = [];
  const th = Math.floor(n / 1000), h = Math.floor(n % 1000 / 100), r = n % 100;
  if (th) parts.push(th === 1 ? ['alf', 'ألف'] : th === 2 ? ['alfin', 'ألفين'] : [STEM[th][0] + ' alaf', STEM[th][1] + ' ألاف']);
  if (h) parts.push(h === 1 ? ['mya', 'مية'] : h === 2 ? ['mitin', 'ميتين'] : [STEM[h][0] + ' mya', STEM[h][1] + ' مية']);
  if (r && r < 20) parts.push(UNITS[r]);
  else if (r) {
    // 2 is tnin beside a ten (tnin w 3achrin), juj on its own.
    if (r % 10) parts.push(r % 10 === 2 ? ['tnin', 'تنين'] : UNITS[r % 10]);
    parts.push(TENS[Math.floor(r / 10)]);
  }
  return { lat: parts.map(p => p[0]).join(' w '), ar: parts.map(p => p[1]).join(' و ') };
}

const EN_UNITS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen'];
const EN_TENS = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'];
// English name for the round numbers the dictionary lists: 0-19, tens, hundreds, thousands.
export function english(n) {
  return n < 20 ? EN_UNITS[n] : n < 100 ? EN_TENS[n / 10] : n < 1000 ? EN_UNITS[n / 100] + ' hundred' : EN_UNITS[n / 1000] + ' thousand';
}

// Fractions: half, third, quarter, fifth, eighth. The stems are the ones used for hundreds (tlt, rb3, khms, tmn).
export const FRACTIONS = [
  { sym: '1/2', en: 'half', lat: 'nus', ar: 'نص' },
  { sym: '1/3', en: 'third', lat: 'tlt', ar: 'تلت' },
  { sym: '1/4', en: 'quarter', lat: 'rub3', ar: 'ربع' },
  { sym: '1/5', en: 'fifth', lat: 'khums', ar: 'خمس' },
  { sym: '1/8', en: 'eighth', lat: 'tmn', ar: 'تمن' },
];

// Clock times: the hour follows s-sa3a (feminine: wa7da, then the usual numbers). Minutes are 0, 15, 30 or 45:
// "w rub3" past, "w nus" half past, "ila rub3" to the next hour. Noon and midnight have their own words.
const PART = h => (h >= 5 && h < 12 ? ['d s-sba7', 'د الصباح'] : h >= 12 && h < 16 ? ['d z-zwal', 'د الزوال'] : h >= 16 && h < 21 ? ['d l-3chiya', 'د العشية'] : ['d l-lil', 'د الليل']);
export const hourWord = h => (h % 12 === 1 ? { lat: 'wa7da', ar: 'واحدة' } : say(h % 12 || 12));
export function clock(h, m) {
  const mins = { 15: ['w rub3', 'و ربع'], 30: ['w nus', 'و نص'], 45: ['ila rub3', 'الا ربع'] }[m];
  if (!m && h === 12) return { lat: 'z-zwal', ar: 'الزوال', en: 'noon' };
  if (!m && h === 0) return { lat: 'nus l-lil', ar: 'نص الليل', en: 'midnight' };
  const at = m === 45 ? (h + 1) % 24 : h, w = hourWord(at), p = PART(at);
  const h12 = h % 12 || 12;
  return {
    lat: 's-sa3a ' + w.lat + (mins ? ' ' + mins[0] : '') + ' ' + p[0],
    ar: 'الساعة ' + w.ar + (mins ? ' ' + mins[1] : '') + ' ' + p[1],
    en: h12 + ':' + String(m).padStart(2, '0') + (h < 12 ? ' am' : ' pm'),
  };
}
