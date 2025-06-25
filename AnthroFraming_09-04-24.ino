#include "MeMegaPi.h"

// Pins for Bluetooth communication
#define TX_PIN 14
#define RX_PIN 15
#define LED_PIN 13

// Sensor pins
#define LEFT_SENSOR_PIN 69
#define RIGHT_SENSOR_PIN 68

MeMegaPiDCMotor motor1(PORT1B); // Left motor
MeMegaPiDCMotor motor2(PORT2B); // Arm motor
MeMegaPiDCMotor motor3(PORT3B); // Right motor
MeMegaPiDCMotor motor4(PORT4B);

// Motor speeds
uint8_t motorSpeed = 60;
uint8_t motorSpeedB = 42;
uint8_t motorSpeed1 = 61;
uint8_t motorSpeed1B = 44;

// Boost parameters
uint8_t boostSpeed = 100;	// Higher initial speed
uint8_t boostDuration = 50; // Duration of boost in milliseconds

// Correction factor for line following
const float CORRECTION_FACTOR = 1.5; // Increases speed by 50% when correcting

// Chip counter for curve turns
int chipCount = 0;

void setup()
{
	pinMode(LED_PIN, OUTPUT);
	pinMode(LEFT_SENSOR_PIN, INPUT);
	pinMode(RIGHT_SENSOR_PIN, INPUT);
	Serial3.begin(9600);
	Serial3.println("Ready to receive commands.");
}

void stopMotors()
{
	motor1.stop();
	motor3.stop();
}

void quickCenter()
{
	int leftSensor = digitalRead(LEFT_SENSOR_PIN);
	int rightSensor = digitalRead(RIGHT_SENSOR_PIN);

	if (leftSensor == 1 || rightSensor == 1)
	{
		if (leftSensor == 1)
		{
			motor1.run(motorSpeed1);
			motor3.run(motorSpeed);
			delay(50);
		}
		if (rightSensor == 1)
		{
			motor1.run(-motorSpeed1);
			motor3.run(-motorSpeed);
			delay(50);
		}
		stopMotors();
	}
}

void delayWithChecks(int ms)
{
	long startTime = millis();
	while (millis() - startTime < ms)
	{
		quickCenter();
		delay(50);
	}
}

void startMotorsWithBoost(int16_t leftSpeed, int16_t rightSpeed)
{
	motor1.run(leftSpeed > 0 ? boostSpeed : -boostSpeed);
	motor3.run(rightSpeed > 0 ? boostSpeed : -boostSpeed);
	delay(boostDuration);
	motor1.run(leftSpeed);
	motor3.run(rightSpeed);
}

void lowerArm()
{
	stopMotors();
	motor2.run(-motorSpeed);
	delay(1000);
	motor2.stop();
	delayWithChecks(500);
}

void raiseArm()
{
	stopMotors();
	motor2.run(motorSpeed);
	delay(1300);
	motor2.stop();
	delayWithChecks(500);
}

void scanChip()
{
	// Forward scan
	unsigned long startTime = millis();
	const unsigned long FORWARD_SCAN_TIME = 1400;
	bool firstMove = true;

	while (millis() - startTime < FORWARD_SCAN_TIME)
	{
		int leftSensor = digitalRead(LEFT_SENSOR_PIN);
		int rightSensor = digitalRead(RIGHT_SENSOR_PIN);

		if (leftSensor == 0 && rightSensor == 0)
		{
			if (firstMove)
			{
				startMotorsWithBoost(motorSpeed1B, -motorSpeedB);
				firstMove = false;
			}
			else
			{
				motor1.run(motorSpeed1B);
				motor3.run(-motorSpeedB);
			}
		}
		else if (leftSensor == 1 && rightSensor == 0)
		{
			motor1.run(motorSpeed1B * CORRECTION_FACTOR);
			motor3.run(-motorSpeedB);
		}
		else if (leftSensor == 0 && rightSensor == 1)
		{
			motor1.run(motorSpeed1B);
			motor3.run(-motorSpeedB * CORRECTION_FACTOR);
		}
		else
		{
			motor1.run(motorSpeed1B);
			motor3.run(-motorSpeedB);
		}
		delay(10);
	}

	stopMotors();
	delayWithChecks(500);

	// Backward scan
	startTime = millis();
	const unsigned long BACKWARD_SCAN_TIME = 1350;
	firstMove = true;

	while (millis() - startTime < BACKWARD_SCAN_TIME)
	{
		int leftSensor = digitalRead(LEFT_SENSOR_PIN);
		int rightSensor = digitalRead(RIGHT_SENSOR_PIN);

		if (leftSensor == 0 && rightSensor == 0)
		{
			if (firstMove)
			{
				startMotorsWithBoost(-motorSpeed1B, motorSpeedB);
				firstMove = false;
			}
			else
			{
				motor1.run(-motorSpeed1B);
				motor3.run(motorSpeedB);
			}
		}
		else if (leftSensor == 1 && rightSensor == 0)
		{
			motor1.run(-motorSpeed1B * CORRECTION_FACTOR);
			motor3.run(motorSpeedB);
		}
		else if (leftSensor == 0 && rightSensor == 1)
		{
			motor1.run(-motorSpeed1B);
			motor3.run(motorSpeedB * CORRECTION_FACTOR);
		}
		else
		{
			motor1.run(-motorSpeed1B);
			motor3.run(motorSpeedB);
		}
		delay(10);
	}

	stopMotors();
	delayWithChecks(500);
}

/**
 * CURVE FUNCTION
 * This controls the behavior of the turning / taxi to a new row
 * A curve begins when the chipCount reaches one of the assigned values { See section: CHIPS PER ROW }
 * Section B. Describes when the curve knows to stop when encountering a horizontal line
 */
void curveTurn()
{
	const int TURN_SPEED = 100; // High speed for both motors
	Serial3.println("Starting curve turn sequence");

	while (true)
	{
		int leftSensor = digitalRead(LEFT_SENSOR_PIN);
		int rightSensor = digitalRead(RIGHT_SENSOR_PIN);

		// B. STOPS WHEN BOTH SENSORS HIT A LINE AT THE SAME TIME
		if (leftSensor == 1 && rightSensor == 1)
		{
			Serial3.println("End of curve detected");
			motor1.stop();
			motor3.stop();
			break;
		}

		// Curve following behavior
		if (leftSensor == 1 && rightSensor == 0)
		{
			// Left sensor on line - sharp right turn
			motor1.run(TURN_SPEED); // Left wheel forward
			motor3.run(TURN_SPEED); // Right wheel reverse
		}
		else if (leftSensor == 0 && rightSensor == 1)
		{
			// Right sensor on line - sharp left turn
			motor1.run(-TURN_SPEED); // Left wheel reverse
			motor3.run(-TURN_SPEED); // Right wheel forward
		}
		else if (leftSensor == 0 && rightSensor == 0)
		{
			// Both off line - go straight
			motor1.run(TURN_SPEED);
			motor3.run(-TURN_SPEED);
		}

		delay(10);
	}
}

void nextChip()
{
	chipCount++;
	Serial3.print("Chip count: ");
	Serial3.println(chipCount);

	/**
	 * CHIPS PER ROW
	 * 10 is the number of chips before the first curve
	 * then 20 is the next row, assuming 10 chips before each turn.
	 *
	 * Change these values to match the number of chips from the start
	 * for each turn.
	 *
	 * To add turns add " || chipCount == X " for as many turns as you need.
	 */
	if (chipCount == 10 || chipCount == 20)
	{
		Serial3.println("Executing curve turn");
		curveTurn();
		return;
	}

	unsigned long startTime = millis();
	const unsigned long NEXT_CHIP_TIME = 800;
	bool firstMove = true;
	bool bothSensorsTriggered = false;

	while (millis() - startTime < NEXT_CHIP_TIME)
	{
		int leftSensor = digitalRead(LEFT_SENSOR_PIN);
		int rightSensor = digitalRead(RIGHT_SENSOR_PIN);

		if (leftSensor == 0 && rightSensor == 0)
		{
			if (firstMove)
			{
				startMotorsWithBoost(motorSpeed1, -motorSpeed);
				firstMove = false;
			}
			else
			{
				motor1.run(motorSpeed1);
				motor3.run(-motorSpeed);
			}
		}
		else if (leftSensor == 1 && rightSensor == 0)
		{
			motor1.run(motorSpeed1 * CORRECTION_FACTOR);
			motor3.run(-motorSpeed);
		}
		else if (leftSensor == 0 && rightSensor == 1)
		{
			motor1.run(motorSpeed1);
			motor3.run(-motorSpeed * CORRECTION_FACTOR);
		}

		delay(10);
	}

	stopMotors();
	delayWithChecks(500);
}

void loop()
{
	if (Serial3.available() > 0)
	{
		char command = Serial3.read();

		switch (command)
		{
		case '1':
			digitalWrite(LED_PIN, HIGH);
			scanChip();
			digitalWrite(LED_PIN, LOW);
			Serial3.println("Normal Motor sequence complete.");
			break;

		case '2':
			digitalWrite(LED_PIN, HIGH);
			lowerArm();
			scanChip();
			raiseArm();
			digitalWrite(LED_PIN, LOW);
			Serial3.println("Zoomed Motor sequence complete.");
			break;

		case '3':
			digitalWrite(LED_PIN, HIGH);
			nextChip();
			digitalWrite(LED_PIN, LOW);
			Serial3.println("Next chip command complete.");
			break;

		default:
			Serial3.println("Unknown command");
			break;
		}
	}
}
