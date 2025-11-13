"""
PHASE 1 SUBFINDER ENVIRONMENT - TEST SUITE
==========================================

Comprehensive tests for SubfinderEnv implementation.
Validates all core functionality before training.
"""

import pytest
import numpy as np
from pathlib import Path
import sys
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from envs.subfinder_env import SubfinderEnv


@pytest.fixture
def env():
    """Create environment for testing"""
    scenarios_path = Path(__file__).parent.parent.parent / "data/scenarios/phase1_training.json"
    return SubfinderEnv(scenarios_path=str(scenarios_path))


class TestEnvironmentInstantiation:
    """Test 1: Environment instantiates without errors"""
    
    def test_environment_creation(self, env):
        """Environment should be created successfully"""
        assert env is not None
        assert hasattr(env, 'observation_space')
        assert hasattr(env, 'action_space')
    
    def test_scenarios_loaded(self, env):
        """Scenarios should be loaded"""
        assert len(env.scenarios) > 0
        assert len(env.scenarios) == 10  # Training set has 10 scenarios


class TestObservationSpace:
    """Test 2: Reset returns valid observation"""
    
    def test_reset_returns_observation(self, env):
        """Reset should return observation and info"""
        obs, info = env.reset()
        assert obs is not None
        assert info is not None
        assert isinstance(info, dict)
    
    def test_observation_shape(self, env):
        """Observation should be 15-dimensional"""
        obs, _ = env.reset()
        assert obs.shape == (15,)
    
    def test_observation_range(self, env):
        """Observation values should be in [0, 1] range"""
        obs, _ = env.reset()
        assert np.all(obs >= 0.0)
        assert np.all(obs <= 1.0)
    
    def test_observation_dtype(self, env):
        """Observation should be float32"""
        obs, _ = env.reset()
        assert obs.dtype == np.float32


class TestActionSpace:
    """Test 3: Step executes for all 3 actions"""
    
    def test_action_space_size(self, env):
        """Action space should have 3 actions"""
        assert env.action_space.n == 3
    
    def test_all_actions_executable(self, env):
        """All actions should be executable"""
        for action in range(3):
            env.reset()
            obs, reward, terminated, truncated, info = env.step(action)
            assert obs is not None
            assert isinstance(reward, (int, float))
            assert isinstance(terminated, bool)
            assert isinstance(truncated, bool)
            assert isinstance(info, dict)


class TestRewardCalculation:
    """Test 4: Rewards calculated correctly"""
    
    def test_reward_structure(self, env):
        """Reward should have all 4 components"""
        env.reset()
        obs, reward, terminated, truncated, info = env.step(2)  # comprehensive
        
        # Check reward breakdown in info
        assert 'reward_breakdown' in info
        breakdown = info['reward_breakdown']
        
        # All 4 component groups should exist (not necessarily individual keys)
        # Discovery group
        assert 'subdomain_discovery' in breakdown or 'high_value_bonus' in breakdown or 'tech_discovery' in breakdown
        # Efficiency group
        assert 'time_penalty' in breakdown
        # Strategic group (coverage_bonus, efficiency_bonus, etc.)
        assert 'coverage_bonus' in breakdown
        # Completion group
        assert 'completion_bonus' in breakdown
    
    def test_discovery_reward_positive(self, env):
        """Finding subdomains should give positive reward"""
        env.reset()
        
        obs, reward, terminated, truncated, info = env.step(2)  # comprehensive
        
        # Check if new subdomains were found
        if info['new_subdomains_found'] > 0:
            # Should have positive discovery component
            assert info['reward_breakdown']['subdomain_discovery'] > 0
    
    def test_time_penalty_negative(self, env):
        """Time penalty should be negative"""
        env.reset()
        obs, reward, terminated, truncated, info = env.step(2)  # comprehensive (60s)
        
        # Time penalty should be negative
        assert info['reward_breakdown']['time_penalty'] < 0


class TestActionMasking:
    """Test 5: Action masking works"""
    
    def test_action_masks_exist(self, env):
        """Environment should provide action masks"""
        env.reset()
        masks = env.action_masks()
        assert masks is not None
        assert len(masks) == 3
    
    def test_initial_all_actions_valid(self, env):
        """All actions should be valid initially"""
        env.reset()
        masks = env.action_masks()
        assert np.all(masks)  # All True
    
    def test_redundant_action_masked(self, env):
        """Repeated action should be masked"""
        env.reset()
        
        # Use comprehensive
        env.step(2)
        
        # Check mask - comprehensive should now be invalid
        masks = env.action_masks()
        assert not masks[2]  # comprehensive should be False


class TestEpisodeTermination:
    """Test 6: Episode terminates correctly"""
    
    def test_success_termination(self, env):
        """Episode should terminate on success (90%+ coverage)"""
        env.reset()
        
        # Run multiple steps
        for _ in range(10):
            obs, reward, terminated, truncated, info = env.step(2)  # comprehensive
            
            if terminated:
                # Check success condition via total_subdomains_found
                ground_truth = env.current_scenario["ground_truth"]
                total_possible = ground_truth["total_subdomains"]
                coverage = info['total_subdomains_found'] / total_possible
                assert coverage >= 0.9
                break
    
    def test_budget_truncation(self, env):
        """Episode should truncate when budget exceeded"""
        env.reset()
        
        # Force budget exhaustion (simulate long scans)
        for _ in range(20):
            masks = env.action_masks()
            valid_actions = np.where(masks)[0]
            
            if len(valid_actions) == 0:
                break
            
            action = valid_actions[0]
            obs, reward, terminated, truncated, info = env.step(action)
            
            if truncated:
                # Should be due to budget OR max scans (3) OR max steps (10)
                assert (
                    info['time_elapsed'] >= env.time_budget or
                    env.total_scans >= 3 or
                    env.step_count >= 10
                )
                break


class TestPerformance:
    """Test 7: Performance >1000 steps/second"""
    
    def test_step_performance(self, env):
        """Environment should execute >1000 steps/second"""
        # Warm-up
        env.reset()
        for _ in range(100):
            masks = env.action_masks()
            valid_actions = np.where(masks)[0]
            if len(valid_actions) == 0:
                env.reset()
                continue
            env.step(valid_actions[0])
        
        # Measure
        start = time.perf_counter()
        steps = 0
        episodes = 0
        
        while steps < 5000 and episodes < 50:
            env.reset()
            episodes += 1
            
            for _ in range(100):
                masks = env.action_masks()
                valid_actions = np.where(masks)[0]
                
                if len(valid_actions) == 0:
                    break
                
                obs, reward, terminated, truncated, info = env.step(valid_actions[0])
                steps += 1
                
                if terminated or truncated:
                    break
        
        elapsed = time.perf_counter() - start
        steps_per_second = steps / elapsed
        
        print(f"\n⚡ Performance: {steps_per_second:.0f} steps/second")
        print(f"   {steps} steps in {elapsed:.2f}s over {episodes} episodes")
        
        # Target: >1000 steps/second
        assert steps_per_second > 1000, f"Too slow: {steps_per_second:.0f} steps/s (need >1000)"


if __name__ == "__main__":
    # Run with pytest -v
    pytest.main([__file__, "-v", "-s"])
