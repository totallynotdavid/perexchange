import { execFileSync } from "node:child_process";
import path from "node:path";

export const ROOT = path.resolve(import.meta.dirname, "../..");

/** Records two fetches with `tools/snapshot.py`, the same code the scheduled job runs. */
const RECORD = `
import importlib.util, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from perexchange import ExchangeRate, FetchReport, SourceFailure

spec = importlib.util.spec_from_file_location("snapshot", sys.argv[1] + "/tools/snapshot.py")
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)

start = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)

def rate(source, name, buy, sell, age):
    return ExchangeRate(source, name, buy, sell, start - timedelta(minutes=age))

first = FetchReport(
    rates=(
        rate("cambiafx", "cambiafx", 3.435, 3.458, 0),
        rate("cuantoestaeldolar", "Gordito digital", 3.435, 3.455, 0),
        rate("chapacambio", "chapacambio", 3.433, 3.464, 1800),
    ),
    failures=(SourceFailure("mercadocambiario", "HTTPStatusError", "403 Forbidden", 403),),
)
data_dir = Path(sys.argv[2])
snapshot.write_snapshot(first, data_dir, start)
second = FetchReport(
    rates=(rate("cambiafx", "cambiafx", 3.436, 3.45, 0),),
    failures=(SourceFailure("cambiomundial", "HTTPStatusError", "403 Forbidden", 403),),
)
snapshot.write_snapshot(second, data_dir, start + timedelta(minutes=15))
`;

/** Records one fetch with enough houses to exercise the site's overflow layout. */
const RECORD_COMPLETE = `
import importlib.util, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from perexchange import ExchangeRate, FetchReport

spec = importlib.util.spec_from_file_location("snapshot", sys.argv[1] + "/tools/snapshot.py")
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)

start = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
houses = ["cambiafx", "tkambio", "tucambista", "okane", "dolarex", "inkamoney", "inticambio",
          "moneyplus", "srcambio", "masscambio", "metafx", "westernunion"]
rates = [
    ExchangeRate(house, house, 3.43 + i * 0.001, 3.458 + i * 0.002, start)
    for i, house in enumerate(houses)
]
rates.append(ExchangeRate("cuantoestaeldolar", "Gordito digital", 3.435, 3.455, start))
rates.append(ExchangeRate("tkambio", "tkambio_5000", 3.44, 3.45, start))
report = FetchReport(rates=tuple(rates), failures=())
snapshot.write_snapshot(report, Path(sys.argv[2]), start)
`;

function run(script: string, dataDir: string): void {
  execFileSync("uv", ["run", "--project", ROOT, "python", "-c", script, ROOT, dataDir], {
    stdio: "pipe",
  });
}

export function recordSnapshots(dataDir: string): void {
  run(RECORD, dataDir);
}

export function recordCompleteSnapshot(dataDir: string): void {
  run(RECORD_COMPLETE, dataDir);
}
