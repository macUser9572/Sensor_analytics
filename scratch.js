const toISTChartString = (dateInput) => {
  const d = new Date(dateInput);
  const istTime = new Date(d.toLocaleString("en-US", {timeZone: "Asia/Kolkata"}));
  const pad = (n) => n.toString().padStart(2, '0');
  return `${istTime.getFullYear()}-${pad(istTime.getMonth()+1)}-${pad(istTime.getDate())} ${pad(istTime.getHours())}:${pad(istTime.getMinutes())}:${pad(istTime.getSeconds())}`;
};
console.log(toISTChartString("2026-05-06T09:40:21+00:00"));
