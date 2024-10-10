/**
 * \par Copyright (C), 2012-2016, MakeBlock
 * @file    MeMegaPiDCMotorTest.ino
 * @author  MakeBlock
 * @version V1.0.0
 * @date    2016/05/17
 * @brief   Description: this file is sample code for MegaPi DC motor device.
 *
 * Function List:
 *    1. void MeMegaPiDCMotorTest::run(int16_t speed)
 *    2. void MeMegaPiDCMotorTest::stop(void)
 *
 * \par History:
 * <pre>
 * <Author>     <Time>        <Version>      <Descr>
 * Mark Yan     2016/05/17    1.0.0          build the new
 * </pre>
 */
#include "MeMegaPi.h"

MeMegaPiDCMotor motor1(PORT1B);

MeMegaPiDCMotor motor2(PORT2B);

MeMegaPiDCMotor motor3(PORT3B);

MeMegaPiDCMotor motor4(PORT4B);


uint8_t motorSpeed = 60;
uint8_t motorSpeedB = 40;
uint8_t motorSpeed1 = 61;
uint8_t motorSpeed1B = 42;
void setup()
{
}

void loop()
{

  //motor4 = front motor
  //motor2 = back motor

  // Move to chip
  motor1.run(motorSpeed1); /* value: between -255 and 255. */
  //motor2.run(motorSpeed); /* value: between -255 and 255. */
  motor3.run(-motorSpeed);
  delay(3500);

  // Stop in front of chip and lower arm
  motor1.stop();
  //motor2.stop();
  motor3.stop();

  motor2.run(-motorSpeed);
  delay(1500); 
  motor2.stop();

  //Scan chip forward 
  motor1.run(motorSpeed1B);
  motor3.run(-motorSpeedB);
  delay(2500);
  motor1.stop();
  motor3.stop();
  delay(500);

  //Scan chip backwards
  motor1.run(-motorSpeed1B);
  motor3.run(motorSpeedB);
  delay(2500);


  // Finish Scanning and raise arm
  motor1.stop();
  motor3.stop();
  motor2.run(motorSpeed);
  delay(1800);
  motor2.stop();
  delay(500);

  // Move back to starting position
  motor1.run(-motorSpeed1);
  motor3.run(motorSpeed);
  delay(3200);

  // Take a little break buddy. Good Job!
  motor1.stop();
  motor3.stop();
  delay(10000);

}