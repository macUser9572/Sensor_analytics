const d = new Date("2026-05-06T14:44:11Z");
const istTime = new Date(d.toLocaleString("en-US", {timeZone: "Asia/Kolkata"}));
const pad = (n) => n.toString().padStart(2, '0');
const res = `${istTime.getFullYear()}-${pad(istTime.getMonth()+1)}-${pad(istTime.getDate())} ${pad(istTime.getHours())}:${pad(istTime.getMinutes())}:${pad(istTime.getSeconds())}`;
console.log(res);
