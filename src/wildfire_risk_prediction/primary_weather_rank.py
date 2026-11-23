"""Guard a quality-alignment run; preserve the historical broad-support experiments."""

from .feature_join import require


def validate(policy, weather_spec, proposal):
    require(
        policy["decision_source"]
        == "user_long_autonomous_continue_apply_preexisting_weather_primary_profile"
        and policy["new_models"] == 9
        and policy["fit_years"] == [2018, 2019, 2020, 2021]
        and policy["exploratory_assessment_year"] == 2022
        and policy["local_time_limit_seconds"] == 900
        and policy["profile"] == "primary_full_area"
        and policy["weather_policy_version"] == weather_spec["version"] == "weather_model_v1"
        and weather_spec["primary_minimum_valid_area_fraction"] == 1.0,
        "Bounded quality alignment with existing full-area weather rule",
    )
    require(
        all(
            policy[k] is False
            for k in (
                "new_threshold_selected",
                "hyperparameter_search",
                "new_model_family",
                "original_package_changed",
                "true_Y_or_accepted_L_assignment",
                "negative_label_permitted",
                "main_PU_method_scientifically_accepted",
                "closed_year_2023_2024_2025_values_permitted",
                "risk_probability_or_validated_color_output",
                "cloud_permitted",
                "final_merge_permitted",
            )
        )
        and policy["daily_observation_status"] == "unknown"
        and proposal["objective"] == "rank:pairwise"
        and proposal["fixed_parameters_proposed"]["n_estimators"] == 100,
        "No new method claims, future years, labels or parameter search",
    )
