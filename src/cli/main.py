import sys
import argparse
import os
import time
from dotenv import load_dotenv

load_dotenv(override=True)

from src.cli.wiring import (
    build_ingest_use_case,
    build_transform_artifacts_use_case,
    build_transform_oq_use_case,
    build_add_decision_use_case,
    build_modify_oq_use_case,
    build_approve_pu_use_case,
    build_change_artifact_status_use_case,
    build_change_artifact_status_batch_use_case,
    build_list_artifacts_use_case,
    build_list_open_questions_use_case,
    build_list_proposed_updates_use_case,
    build_init_sync_use_case,
    build_reset_data_use_case,
    build_set_last_ts_use_case,
    build_delete_oq_use_case,
    build_delete_oq_batch_use_case,
)

class SpecsUpdatesAgent:
    def __init__(self):
        pass

    def run(self):
        parser = argparse.ArgumentParser(description="Specs Updates Generator CLI")
        subparsers = parser.add_subparsers(dest="command")

        # Command: ingest
        ingest_parser = subparsers.add_parser("ingest", help="Ingest Slack threads and classify artifacts")
        ingest_parser.add_argument("--channel", default=os.getenv("SLACK_CHANNEL_ID", "general"), help="Slack channel ID to ingest from (defaults to SLACK_CHANNEL_ID in .env or 'general')")
        
        # Command: change_status
        status_parser = subparsers.add_parser("change_status", help="Change status of one or more artifacts")
        status_parser.add_argument("artifact_ids", nargs="+", help="Artifact IDs (or IDs followed by status)")
        status_parser.add_argument("--status", choices=["OQ", "PU", "IRRELEVANT"], help="New status")

        # Command: artifact_transform
        subparsers.add_parser("artifact_transform", help="Transform artifacts into OQ or PU")

        # Command: oq_modify
        oq_mod_parser = subparsers.add_parser("oq_modify", help="Modify an Open Question")
        oq_mod_parser.add_argument("oq_id", help="OQ ID")

        # Command: oq_decide
        oq_decide_parser = subparsers.add_parser("oq_decide", help="Add a decision to an Open Question")
        oq_decide_parser.add_argument("oq_id", help="OQ ID")

        # Command: oq_transform
        subparsers.add_parser("oq_transform", help="Transform decided OQs into PUs")

        # Command: oq_delete
        oq_delete_parser = subparsers.add_parser("oq_delete", help="Delete one or more OQs and mark artifacts IRRELEVANT")
        oq_delete_parser.add_argument("oq_ids", nargs="+", help="OQ IDs")
        oq_delete_parser.add_argument("--yes", action="store_true", help="Confirm delete without prompt")

        # Command: approve_pu
        pu_app_parser = subparsers.add_parser("approve_pu", help="Approve a Proposed Update")
        pu_app_parser.add_argument("pu_id", help="PU ID")

        # Command: init_sync
        init_parser = subparsers.add_parser("init_sync", help="Initialize the sync timestamp to current time to skip history")
        init_parser.add_argument("--channel", help="Specific channel ID to initialize (optional, uses .env or --channel)")

        # Command: set_last_ts
        set_ts_parser = subparsers.add_parser("set_last_ts", help="Set last_ts by days back from now")
        set_ts_parser.add_argument("--channel", help="Specific channel ID to set (optional, uses .env or --channel)")
        set_ts_parser.add_argument("--days", type=float, help="Number of days back (e.g. 3)")

        # Command: reset_data
        reset_parser = subparsers.add_parser("reset_data", help="Reset stored JSON data")
        reset_parser.add_argument("--yes", action="store_true", help="Confirm reset without prompt")

        # Command: art_list
        subparsers.add_parser("art_list", help="List all artifacts")

        # Command: oq_list
        subparsers.add_parser("oq_list", help="List all open questions")

        # Command: pu_list
        subparsers.add_parser("pu_list", help="List all proposed updates")

        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return

        self.handle_command(args)

    def handle_command(self, args):
        # Dispatch command to method
        method_name = f"cmd_{args.command}"
        if hasattr(self, method_name):
            getattr(self, method_name)(args)
        else:
            print(f"Command {args.command} not implemented yet.")

    def cmd_ingest(self, args):
        channel_id = args.channel
        print(f"Ingesting Slack threads from {channel_id}...")
        
        ingest_use_case = build_ingest_use_case()
        result = ingest_use_case.execute(channel_id)
        if result.threads_fetched == 0:
            print("No new threads found.")
            return
        artifacts_created = result.artifacts_created

        if artifacts_created > 0:
            print(
                "Successfully created "
                f"{artifacts_created} new artifacts "
                f"(OQ: {result.oq_count}, PU: {result.pu_count}, IRRELEVANT: {result.irrelevant_count})."
            )
        else:
            print("No new artifacts found in the ingested threads.")

    def cmd_change_status(self, args):
        status_choices = {"OQ", "PU", "IRRELEVANT"}
        status = args.status
        artifact_ids = list(args.artifact_ids)

        if status is None:
            if not artifact_ids or artifact_ids[-1] not in status_choices:
                print("Missing status. Provide --status or pass status as the last argument.")
                return
            status = artifact_ids[-1]
            artifact_ids = artifact_ids[:-1]

        if not artifact_ids:
            print("No artifact IDs provided.")
            return

        print(f"Changing status of {len(artifact_ids)} artifact(s) to {status}...")
        use_case = build_change_artifact_status_batch_use_case()
        result = use_case.execute(artifact_ids, status)

        if result.missing_ids:
            print(f"Not found: {', '.join(result.missing_ids)}")

        if result.updated_ids:
            print(f"Updated: {', '.join(result.updated_ids)}")

    def cmd_artifact_transform(self, args):
        print("Transforming artifacts...")
        use_case = build_transform_artifacts_use_case()

        oq_count, pu_count = use_case.execute()
        print(f"Created {oq_count} Open Questions and {pu_count} Proposed Updates.")
        
    def cmd_oq_transform(self, args):
        print("Transforming decided OQs to PUs...")
        use_case = build_transform_oq_use_case()
        result = use_case.execute()

        print(f"Created {result.transformed_count} Proposed Updates.")
        if result.open_questions_remaining == 0 and result.transformed_count > 0:
            print("All OQs processed.")

    def cmd_oq_decide(self, args):
        print(f"Adding decision to OQ {args.oq_id}...")
        decision = input("Enter the decision for this OQ: ")
        rationale = input("Enter the rationale: ")

        use_case = build_add_decision_use_case()
        result = use_case.execute(args.oq_id, decision, rationale)

        if not result.updated:
            print(f"OQ {args.oq_id} not found.")
            return

        print(f"Decision saved for OQ {args.oq_id}.")

    def cmd_oq_delete(self, args):
        oq_ids = list(args.oq_ids)
        if not oq_ids:
            print("No OQ IDs provided.")
            return

        if not args.yes:
            plural = "s" if len(oq_ids) > 1 else ""
            confirm = input(
                f"Delete {len(oq_ids)} OQ{plural} and mark artifact(s) IRRELEVANT? (y/n): "
            ).strip().lower()
            if confirm not in {"y", "yes"}:
                print("Delete cancelled.")
                return

        use_case = build_delete_oq_batch_use_case()
        result = use_case.execute(oq_ids)

        if result.missing_ids:
            print(f"Not found: {', '.join(result.missing_ids)}")

        if result.deleted_ids:
            print(f"Deleted: {', '.join(result.deleted_ids)}")

    def cmd_approve_pu(self, args):
        print(f"Approving PU {args.pu_id}...")
        use_case = build_approve_pu_use_case()
        result = use_case.execute(args.pu_id)

        if not result.spec_update:
            print(f"PU {args.pu_id} not found.")
            return

        print(f"Spec Update {result.spec_update.id} created.")
        if result.remaining_drafts == 0:
            print("All PUs processed.")

    def cmd_oq_modify(self, args):
        oq_repo = JsonOpenQuestionRepository()
        oq = oq_repo.get_by_id(args.oq_id)
        if not oq:
            print(f"OQ {args.oq_id} not found.")
            return

        print(f"Modifying OQ {args.oq_id}...")

        def ask_yes_no(prompt):
            answer = input(f"{prompt} (y/n): ").strip().lower()
            return answer in {"y", "yes"}

        updates = {}
        print(f"Current question: {oq.question}")
        if ask_yes_no("Do you want to modify the question"):
            updates["question"] = input("New question: ")
        print(f"Current context: {oq.context}")
        if ask_yes_no("Do you want to modify the context"):
            updates["context"] = input("New context: ")
        print(f"Current decision: {oq.decision or ''}")
        if ask_yes_no("Do you want to modify the decision"):
            updates["decision"] = input("New decision: ")
        print(f"Current decision rationale: {oq.decision_rationale or ''}")
        if ask_yes_no("Do you want to modify the decision rationale"):
            updates["decision_rationale"] = input("New decision rationale: ")

        if not updates:
            print("No changes made.")
            return

        use_case = build_modify_oq_use_case()
        result = use_case.execute(args.oq_id, **updates)

        if not result.updated:
            print(f"OQ {args.oq_id} not found.")
            return

        print(f"OQ {args.oq_id} updated.")

    def cmd_init_sync(self, args):
        channel_id = args.channel or os.getenv("SLACK_CHANNEL_ID", "general")
        current_ts = str(time.time())

        use_case = build_init_sync_use_case()
        use_case.execute(channel_id, current_ts)
        
        print(f"Sync initialized for channel {channel_id} at timestamp {current_ts}.")
        print("Future 'ingest' commands will only fetch messages from this point forward.")

    def cmd_set_last_ts(self, args):
        channel_id = args.channel or os.getenv("SLACK_CHANNEL_ID", "general")
        days = args.days
        if days is None:
            raw = input("Enter number of days back (e.g. 3): ").strip()
            try:
                days = float(raw)
            except ValueError:
                print("Invalid number of days.")
                return

        if days < 0:
            print("Days must be a non-negative number.")
            return

        use_case = build_set_last_ts_use_case()
        result = use_case.execute(channel_id, days)
        print(f"Set last_ts for channel {channel_id} to {result.last_ts}.")

    def cmd_art_list(self, args):
        use_case = build_list_artifacts_use_case()
        artifacts = use_case.execute()
        if not artifacts:
            print("No artifacts found.")
            return
        print(f"{'ID':<15} {'Type':<12} {'Status':<15} {'Rephrasing'}")
        print("-" * 85)
        for art in artifacts:
            rephrasing = art.rephrasing or "N/A"
            if len(rephrasing) > 60:
                rephrasing = rephrasing[:57] + "..."
            art_type = art.type.value if hasattr(art.type, "value") else str(art.type)
            print(f"{art.id:<15} {art_type:<12} {art.status:<15} {rephrasing}")

    def cmd_oq_list(self, args):
        use_case = build_list_open_questions_use_case()
        questions = use_case.execute()
        if not questions:
            print("No open questions found.")
            return
        print(f"{'ID':<25} {'Status':<15} {'Decided':<10} {'Question'}")
        print("-" * 95)
        for oq in questions:
            question = oq.question or "N/A"
            if len(question) > 60:
                question = question[:57] + "..."
            decision = oq.decision
            rationale = oq.decision_rationale
            decided = "YES" if decision and rationale and str(decision).strip() and str(rationale).strip() else "NO"
            print(f"{oq.id:<25} {oq.status:<15} {decided:<10} {question}")

    def cmd_pu_list(self, args):
        use_case = build_list_proposed_updates_use_case()
        updates = use_case.execute()
        if not updates:
            print("No proposed updates found.")
            return
        print(f"{'ID':<25} {'Status':<15} {'Rephrasing'}")
        print("-" * 80)
        for pu in updates:
            rephrasing = pu.rephrasing or "N/A"
            if len(rephrasing) > 60:
                rephrasing = rephrasing[:57] + "..."
            print(f"{pu.id:<25} {pu.status:<15} {rephrasing}")

    def cmd_reset_data(self, args):
        if not args.yes:
            confirm = input("This will clear all data JSON files. Continue? (y/n): ").strip().lower()
            if confirm not in {"y", "yes"}:
                print("Reset cancelled.")
                return

        use_case = build_reset_data_use_case()
        result = use_case.execute()
        if result.success:
            print("Data reset completed.")

def main():
    agent = SpecsUpdatesAgent()
    agent.run()


if __name__ == "__main__":
    main()
