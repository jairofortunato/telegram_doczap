#!/usr/bin/env python3
"""
Test deduplication system for WhatsApp and Telegram webhooks
Ensures that duplicate audio messages are not processed multiple times
"""

import asyncio
import time
from utils.processing_state import ProcessingStateManager
from loguru import logger

def test_processing_state_manager():
    """Test the ProcessingStateManager deduplication logic"""
    print("\n" + "="*70)
    print("🧪 Testing ProcessingStateManager Deduplication")
    print("="*70)

    # Initialize manager with short cleanup interval for testing
    manager = ProcessingStateManager(cleanup_interval=5)

    test_file_id = "test_audio_12345"
    all_tests_passed = True

    # Test 1: First processing should succeed
    print("\n📝 Test 1: First processing attempt should succeed")
    result = manager.start_processing(test_file_id)
    if result:
        print("✅ PASS: First processing started successfully")
    else:
        print("❌ FAIL: First processing should have succeeded")
        all_tests_passed = False

    # Test 2: Duplicate processing should fail (already processing)
    print("\n📝 Test 2: Duplicate processing should be blocked (already processing)")
    result = manager.start_processing(test_file_id)
    if not result:
        print("✅ PASS: Duplicate processing blocked correctly")
    else:
        print("❌ FAIL: Duplicate processing should have been blocked")
        all_tests_passed = False

    # Test 3: Check is_processing returns True
    print("\n📝 Test 3: is_processing should return True")
    if manager.is_processing(test_file_id):
        print("✅ PASS: is_processing correctly returns True")
    else:
        print("❌ FAIL: is_processing should return True")
        all_tests_passed = False

    # Test 4: Mark as finished
    print("\n📝 Test 4: Mark processing as finished")
    manager.finish_processing(test_file_id, success=True)
    print("✅ Processing marked as finished")

    # Test 5: Check is_completed returns True
    print("\n📝 Test 5: is_completed should return True")
    if manager.is_completed(test_file_id):
        print("✅ PASS: is_completed correctly returns True")
    else:
        print("❌ FAIL: is_completed should return True")
        all_tests_passed = False

    # Test 6: Processing again should fail (recently completed)
    print("\n📝 Test 6: Processing again should be blocked (recently completed)")
    result = manager.start_processing(test_file_id)
    if not result:
        print("✅ PASS: Processing blocked for recently completed file")
    else:
        print("❌ FAIL: Should not allow processing recently completed file")
        all_tests_passed = False

    # Test 7: Check stats
    print("\n📝 Test 7: Check processing stats")
    stats = manager.get_stats()
    print(f"Stats: {stats}")
    if stats['recently_completed'] == 1 and stats['currently_processing'] == 0:
        print("✅ PASS: Stats are correct")
    else:
        print("❌ FAIL: Stats should show 1 completed, 0 processing")
        all_tests_passed = False

    # Test 8: Test cleanup after timeout
    print("\n📝 Test 8: Test cleanup after timeout (waiting 6 seconds...)")
    time.sleep(6)  # Wait for cleanup interval
    manager.cleanup_old_entries()

    if not manager.is_completed(test_file_id):
        print("✅ PASS: Old completed entry cleaned up")
    else:
        print("❌ FAIL: Old entry should have been cleaned up")
        all_tests_passed = False

    # Test 9: Can process again after cleanup
    print("\n📝 Test 9: Should allow processing again after cleanup")
    result = manager.start_processing(test_file_id)
    if result:
        print("✅ PASS: Processing allowed after cleanup")
        manager.finish_processing(test_file_id, success=True)
    else:
        print("❌ FAIL: Should allow processing after cleanup")
        all_tests_passed = False

    # Test 10: Test concurrent different files
    print("\n📝 Test 10: Test concurrent processing of different files")
    file1 = "audio_001"
    file2 = "audio_002"

    result1 = manager.start_processing(file1)
    result2 = manager.start_processing(file2)

    if result1 and result2:
        print("✅ PASS: Can process multiple different files concurrently")
        manager.finish_processing(file1, success=True)
        manager.finish_processing(file2, success=True)
    else:
        print("❌ FAIL: Should allow concurrent processing of different files")
        all_tests_passed = False

    # Test 11: Test failed processing doesn't block retry
    print("\n📝 Test 11: Failed processing should not block retry")
    failed_file = "failed_audio_123"

    manager.start_processing(failed_file)
    manager.finish_processing(failed_file, success=False)

    # Should be able to retry immediately since it failed
    result = manager.start_processing(failed_file)
    if result:
        print("✅ PASS: Failed processing allows immediate retry")
        manager.finish_processing(failed_file, success=True)
    else:
        print("❌ FAIL: Should allow retry after failed processing")
        all_tests_passed = False

    print("\n" + "="*70)
    if all_tests_passed:
        print("🎉 All deduplication tests PASSED!")
    else:
        print("⚠️  Some deduplication tests FAILED!")
    print("="*70)

    return all_tests_passed


async def test_whatsapp_deduplication_simulation():
    """Simulate WhatsApp duplicate webhook scenario"""
    print("\n" + "="*70)
    print("🧪 Simulating WhatsApp Duplicate Webhook Scenario")
    print("="*70)

    manager = ProcessingStateManager(cleanup_interval=300)

    # Simulate WhatsApp sending the same audio multiple times
    media_id = "whatsapp_audio_abc123xyz"

    print("\n📱 Simulating WhatsApp sending same audio 5 times rapidly...")

    processed_count = 0
    blocked_count = 0

    for i in range(5):
        print(f"\n  Webhook #{i+1}: Attempting to process {media_id}")

        # Check deduplication
        if manager.is_processing(media_id):
            print(f"    ⚠️  Already processing - BLOCKED")
            blocked_count += 1
            continue

        if manager.is_completed(media_id):
            print(f"    ⚠️  Already completed - BLOCKED")
            blocked_count += 1
            continue

        # Try to start processing
        if manager.start_processing(media_id):
            print(f"    ✅ Processing started")
            processed_count += 1

            # Simulate processing time
            await asyncio.sleep(0.5)

            # Mark as finished
            manager.finish_processing(media_id, success=True)
            print(f"    ✅ Processing finished")
        else:
            print(f"    ⚠️  Could not start - BLOCKED")
            blocked_count += 1

    print("\n" + "-"*70)
    print(f"📊 Results:")
    print(f"   Processed: {processed_count} time(s)")
    print(f"   Blocked:   {blocked_count} time(s)")
    print("-"*70)

    if processed_count == 1 and blocked_count == 4:
        print("✅ PASS: Only processed once, blocked 4 duplicates")
        return True
    else:
        print("❌ FAIL: Should process exactly once and block all duplicates")
        return False


async def test_telegram_deduplication_simulation():
    """Simulate Telegram duplicate webhook scenario"""
    print("\n" + "="*70)
    print("🧪 Simulating Telegram Duplicate Webhook Scenario")
    print("="*70)

    manager = ProcessingStateManager(cleanup_interval=300)

    # Simulate Telegram sending the same file_id multiple times
    file_id = "AgADAgADq6cxG1234567890"

    print("\n📱 Simulating Telegram sending same voice message 3 times...")

    processed_count = 0
    blocked_count = 0

    async def process_telegram_voice(attempt_num):
        """Simulate processing a Telegram voice message"""
        nonlocal processed_count, blocked_count

        print(f"\n  Webhook #{attempt_num}: Attempting to process {file_id}")

        # Check deduplication (same as in main.py)
        if manager.is_processing(file_id):
            print(f"    ⚠️  Already processing - BLOCKED")
            blocked_count += 1
            return

        if manager.is_completed(file_id):
            print(f"    ⚠️  Already completed - BLOCKED")
            blocked_count += 1
            return

        # Try to start processing
        if not manager.start_processing(file_id):
            print(f"    ⚠️  Could not start - BLOCKED")
            blocked_count += 1
            return

        print(f"    ✅ Processing started")
        processed_count += 1

        try:
            # Simulate processing time
            await asyncio.sleep(1.0)
            print(f"    ✅ Processing finished successfully")
            manager.finish_processing(file_id, success=True)
        except Exception as e:
            print(f"    ❌ Processing failed: {e}")
            manager.finish_processing(file_id, success=False)

    # Simulate 3 webhook calls in quick succession
    await process_telegram_voice(1)
    await process_telegram_voice(2)
    await process_telegram_voice(3)

    print("\n" + "-"*70)
    print(f"📊 Results:")
    print(f"   Processed: {processed_count} time(s)")
    print(f"   Blocked:   {blocked_count} time(s)")
    print("-"*70)

    if processed_count == 1 and blocked_count == 2:
        print("✅ PASS: Only processed once, blocked 2 duplicates")
        return True
    else:
        print("❌ FAIL: Should process exactly once and block all duplicates")
        return False


async def main():
    """Run all deduplication tests"""
    print("\n" + "="*70)
    print("🚀 DEDUPLICATION TEST SUITE")
    print("="*70)

    results = []

    # Test 1: Basic ProcessingStateManager
    print("\n\n" + "🔹"*35)
    result1 = test_processing_state_manager()
    results.append(("ProcessingStateManager Unit Tests", result1))

    # Test 2: WhatsApp deduplication
    print("\n\n" + "🔹"*35)
    result2 = await test_whatsapp_deduplication_simulation()
    results.append(("WhatsApp Deduplication Simulation", result2))

    # Test 3: Telegram deduplication
    print("\n\n" + "🔹"*35)
    result3 = await test_telegram_deduplication_simulation()
    results.append(("Telegram Deduplication Simulation", result3))

    # Final summary
    print("\n\n" + "="*70)
    print("📊 FINAL TEST SUMMARY")
    print("="*70)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(result for _, result in results)

    print("="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Deduplication is working correctly.")
        print("\n✅ The fix prevents duplicate prontuários from being created.")
        print("✅ Both Telegram and WhatsApp are protected against duplicates.")
    else:
        print("⚠️  SOME TESTS FAILED! Review the output above.")
    print("="*70)

    return all_passed


if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
