import json
import logging
from pathlib import Path

from pydantic import TypeAdapter

from app.database.session import get_session
from app.ingest.jobs.upsert_subscription import upsert_subscriptions
from app.ingest.operations.subscriptions import SubscriptionInput

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SUBSCRIPTIONS_PATH = REPO_ROOT / "data" / "input" / "subscriptions.json"
SUBSCRIPTION_INPUTS = TypeAdapter(list[SubscriptionInput])


def load_subscription_inputs(path: Path) -> list[SubscriptionInput]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return SUBSCRIPTION_INPUTS.validate_python(raw)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    subscriptions_path = DEFAULT_SUBSCRIPTIONS_PATH
    payloads = load_subscription_inputs(subscriptions_path)

    print("Seeding subscriptions from:", subscriptions_path)
    print("  entries:", len(payloads))

    with get_session() as session:
        result = upsert_subscriptions(session, payloads)
        session.commit()

    print("  created:", result.created)
    print("  already existed:", result.existing)
    print("  enriched:", result.enriched)
    if result.failed:
        print("  failed:", len(result.failed))
        for external_id, error in result.failed:
            print(f"    {external_id}: {error}")
