import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

const COLORS = ["#3B4FE0", "#2F855A", "#C67C1E", "#12172B", "#8B95A8"];

export function AllocationDonut({ allocation }: { allocation: Record<string, number> }) {
  const data = Object.entries(allocation).map(([name, value]) => ({ name, value }));

  if (!data.length) {
    return (
      <div className="flex h-56 items-center justify-center text-sm text-slate-soft">
        No holdings yet
      </div>
    );
  }

  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={80}
            paddingAngle={2}
          >
            {data.map((entry, index) => (
              <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => `${Number(value).toFixed(1)}%`} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
