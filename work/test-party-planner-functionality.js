const fs = require("fs");

const html = fs.readFileSync("outputs/nvidia-retirement-party-planner.html", "utf8");
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map((match) => match[1]);

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

for (const script of scripts) {
  new Function(script);
}

assert(html.includes('id="planner"'), "planner section should exist");
assert(html.includes('id="plannerForm"'), "planner form should exist");
assert(html.includes('id="plannerOutput"'), "planner output should exist");
assert(html.includes('name="eventDate"'), "planner should capture event date");
assert(html.includes('name="plannerTone"'), "planner should capture celebration tone");
assert(html.includes('data-planner-moment="cake"'), "planner should include cake moment");
assert(html.includes('data-planner-moment="photo"'), "planner should include photo moment");
assert(html.includes('data-planner-moment="music"'), "planner should include music moment");
assert(html.includes('data-planner-moment="giveaway"'), "planner should include giveaway moment");
assert(html.includes("function buildPlannerPlan"), "planner should build a plan from selected inputs");
assert(html.includes("function renderPlannerPlan"), "planner should render a checklist");
assert(html.includes("function plannerBriefText"), "planner should create copyable brief text");

console.log("party planner functionality checks passed");
