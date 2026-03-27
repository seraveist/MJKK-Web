/**
 * statsConfig.js — 통계 표시 설정 (v3)
 * [변경] richi_yifa.per (일발율) 추가
 */

const display_keys = {
  // ── 기본 ──
  "games":              { label: "대국 수",           format: "int",     category: "기본", higherIsBetter: null },
  "kuksu":              { label: "총합 국 수",        format: "int",     category: "기본", higherIsBetter: null },
  "kuksuji":            { label: "국 수지",           format: "int",     category: "기본", higherIsBetter: true },
  "total.avg":          { label: "평균순위",          format: "float",   category: "기본", higherIsBetter: false },
  "total_first_count":  { label: "1위 횟수",          format: "int",     category: "기본", higherIsBetter: null },
  "total_second_count": { label: "2위 횟수",          format: "int",     category: "기본", higherIsBetter: null },
  "total_third_count":  { label: "3위 횟수",          format: "int",     category: "기본", higherIsBetter: null },
  "total_fourth_count": { label: "4위 횟수",          format: "int",     category: "기본", higherIsBetter: null },
  "first_rate":         { label: "1위율",             format: "percent", category: "기본", higherIsBetter: true },
  "second_rate":        { label: "2위율",             format: "percent", category: "기본", higherIsBetter: null },
  "third_rate":         { label: "3위율",             format: "percent", category: "기본", higherIsBetter: null },
  "fourth_rate":        { label: "4위율",             format: "percent", category: "기본", higherIsBetter: false },
  "endScore.avg":       { label: "최종 점수 평균",    format: "int",     category: "기본", higherIsBetter: true },
  "endScore.max":       { label: "최종 점수 최고",    format: "int",     category: "기본", higherIsBetter: true },
  "endScore.min":       { label: "최종 점수 최저",    format: "int",     category: "기본", higherIsBetter: null },
  "minusScore.avg":     { label: "토비율",            format: "percent", category: "기본", higherIsBetter: false },
  "minusOther.avg":     { label: "타가 들통률",       format: "percent", category: "기본", higherIsBetter: true },
  "east.avg":           { label: "동 시작 평균 순위", format: "float",   category: "기본", higherIsBetter: false },
  "south.avg":          { label: "남 시작 평균 순위", format: "float",   category: "기본", higherIsBetter: false },
  "west.avg":           { label: "서 시작 평균 순위", format: "float",   category: "기본", higherIsBetter: false },
  "north.avg":          { label: "북 시작 평균 순위", format: "float",   category: "기본", higherIsBetter: false },

  // ── 화료 및 방총 ──
  "winGame.avg":         { label: "화료율",           format: "percent", category: "화료 및 방총", higherIsBetter: true },
  "winGame_score.avg":   { label: "평균 타점",        format: "int",     category: "화료 및 방총", higherIsBetter: true },
  "winGame_score.max":   { label: "최대 타점",        format: "int",     category: "화료 및 방총", higherIsBetter: true },
  "winGame_host.per":    { label: "친 화료율",        format: "percent", category: "화료 및 방총", higherIsBetter: true },
  "winGame_zimo.per":    { label: "쯔모율",           format: "percent", category: "화료 및 방총", higherIsBetter: true },
  "winGame_rong.per":    { label: "론율",             format: "percent", category: "화료 및 방총", higherIsBetter: null },
  "winGame_dama.per":    { label: "다마 화료율",      format: "percent", category: "화료 및 방총", higherIsBetter: null },
  "winGame_round.avg":   { label: "평균 화료 순",     format: "float",   category: "화료 및 방총", higherIsBetter: false },
  "chong.avg":           { label: "방총률",           format: "percent", category: "화료 및 방총", higherIsBetter: false },
  "chong_score.avg":     { label: "평균 방총점수",    format: "int",     category: "화료 및 방총", higherIsBetter: null },
  "chong_richi.per":     { label: "리치시 방총률",    format: "percent", category: "화료 및 방총", higherIsBetter: false },
  "chong_fulu.per":      { label: "후로시 방총률",    format: "percent", category: "화료 및 방총", higherIsBetter: false },

  // ── 리치 및 후로 ──
  "richi.avg":           { label: "리치율",           format: "percent", category: "리치 및 후로", higherIsBetter: null },
  "richi_score.avg":     { label: "리치 수지",        format: "int",     category: "리치 및 후로", higherIsBetter: true },
  "richi_winGame.per":   { label: "리치 화료율",      format: "percent", category: "리치 및 후로", higherIsBetter: true },
  "richi_yifa.per":      { label: "일발율",           format: "percent", category: "리치 및 후로", higherIsBetter: true },
  "richi_chong.per":     { label: "리치 방총률",      format: "percent", category: "리치 및 후로", higherIsBetter: false },
  "richi_machi.per":     { label: "리치 다면율",      format: "percent", category: "리치 및 후로", higherIsBetter: true },
  "richi_first.per":     { label: "리치 선제율",      format: "percent", category: "리치 및 후로", higherIsBetter: true },
  "fulu.avg":            { label: "후로율",           format: "percent", category: "리치 및 후로", higherIsBetter: null },
  "fulu_score.avg":      { label: "후로 수지",        format: "int",     category: "리치 및 후로", higherIsBetter: true },
  "fulu_zimo.per":       { label: "후로시 쯔모율",    format: "percent", category: "리치 및 후로", higherIsBetter: true },
  "fulu_rong.per":       { label: "후로시 론율",      format: "percent", category: "리치 및 후로", higherIsBetter: null },
  "fulu_chong.per":      { label: "후로시 방총률",    format: "percent", category: "리치 및 후로", higherIsBetter: false },

  // ── 도라 ──
  "dora.avg":            { label: "평균 전체 도라",   format: "float",   category: "도라", higherIsBetter: true },
  "dora_outer.avg":      { label: "평균 도라",        format: "float",   category: "도라", higherIsBetter: true },
  "dora_akai.avg":       { label: "평균 적도라",      format: "float",   category: "도라", higherIsBetter: true },
  "dora_inner.avg":      { label: "평균 뒷도라",      format: "float",   category: "도라", higherIsBetter: true },
  "dora.per":            { label: "전체 도라율",      format: "percent", category: "도라", higherIsBetter: true },
  "dora_outer.per":      { label: "일반 도라율",      format: "percent", category: "도라", higherIsBetter: true },
  "dora_akai.per":       { label: "적도라율",         format: "percent", category: "도라", higherIsBetter: true },
  "dora_inner.per":      { label: "뒷도라율",         format: "percent", category: "도라", higherIsBetter: true },
  "dora.max":            { label: "최대 전체 도라",   format: "int",     category: "도라", higherIsBetter: null },
  "dora_outer.max":      { label: "최대 도라",        format: "int",     category: "도라", higherIsBetter: null },
  "dora_akai.max":       { label: "최대 적도라",      format: "int",     category: "도라", higherIsBetter: null },
  "dora_inner.max":      { label: "최대 뒷도라",      format: "int",     category: "도라", higherIsBetter: null },
  "dora_inner_eff.avg":  { label: "뒷도라 평균 변화점", format: "int",   category: "도라", higherIsBetter: true },
  "dora_inner_eff.per":  { label: "뒷도라 유효율",    format: "percent", category: "도라", higherIsBetter: true },
  "dora_inner_eff.max":  { label: "뒷도라 최대 변화점", format: "int",   category: "도라", higherIsBetter: null },
};

const CATEGORIES = [...new Set(Object.values(display_keys).map(v => v.category))];

const yaku_name_map = {
  "門前清自摸和": "멘젠쯔모", "立直": "리치", "一発": "일발",
  "槍槓": "창깡", "嶺上開花": "영상개화", "海底摸月": "해저로월",
  "河底撈魚": "하저로어", "平和": "핑후", "断幺九": "탕야오",
  "一盃口": "이페코", "自風 東": "자풍 동", "自風 南": "자풍 남",
  "自風 西": "자풍 서", "自風 北": "자풍 북", "場風 東": "장풍 동",
  "場風 南": "장풍 남", "役牌 白": "역패 백", "役牌 發": "역패 발",
  "役牌 中": "역패 중", "両立直": "더블리치", "七対子": "치또이",
  "混全帯幺九": "찬타", "一気通貫": "일기통관",
  "三色同順": "삼색동순", "三色同刻": "삼색동각",
  "三暗刻": "산안커", "対々和": "또이또이", "三杠子": "산깡즈",
  "混老頭": "혼노두", "小三元": "소삼원", "二盃口": "량페코",
  "純全帯幺九": "준찬타", "混一色": "혼일색", "清一色": "청일색",
  "天和": "천화", "地和": "지화", "国士無双": "국사무쌍",
  "四暗刻": "스안커", "大三元": "대삼원", "小四喜": "소사희",
  "大四喜": "대사희", "字一色": "자일색", "緑一色": "녹일색",
  "清老頭": "청노두", "九蓮宝燈": "구련보등",
  "国士無双十三面待ち": "국사무쌍 13면 대기",
  "四暗刻単騎": "스안커 단기", "純正九蓮宝燈": "순정구련보등",
  "流し満貫": "유국 만관", "数え役満": "헤아림 역만",
};

function getNestedValue(obj, path) {
  return path.split('.').reduce((o, k) => (o ? o[k] : undefined), obj);
}

function formatValue(value, format) {
  if (typeof value !== "number" || isNaN(value)) return "-";
  switch (format) {
    case "int":     return Math.floor(value).toLocaleString();
    case "float":   return value.toFixed(2);
    case "percent": return (value * 100).toFixed(2) + "%";
    default:        return value.toString();
  }
}

function enrichStats(stats) {
  const g = stats.games || 0;
  if (g > 0) {
    stats.first_rate  = (stats.total_first_count  || 0) / g;
    stats.second_rate = (stats.total_second_count || 0) / g;
    stats.third_rate  = (stats.total_third_count  || 0) / g;
    stats.fourth_rate = (stats.total_fourth_count || 0) / g;
  }
  return stats;
}
